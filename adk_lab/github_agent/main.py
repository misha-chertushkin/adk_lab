# adk_lab/github_agent/main.py

import os
import click
import logging
import uvicorn
import asyncio
from dotenv import load_dotenv

# --- Core ADK/MCP Imports ---
from google.adk import Agent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# --- Manual A2A Server Imports ---
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    InternalError,
    InvalidParamsError,
    Part,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_task
from a2a.utils.errors import ServerError

from adk_lab.utils.proxy import GITHUB_TOKEN

# Load environment variables
load_dotenv()


async def _get_agent_async() -> Agent:
    """
    --- NEW HELPER FUNCTION ---
    Asynchronously creates and returns the native ADK Agent for GitHub.
    This consolidates the agent creation logic.
    """
    if not GITHUB_TOKEN:
        raise ValueError("FATAL: GITHUB_PERSONAL_ACCESS_TOKEN secret not found.")

    print("Initializing MCPToolset for GitHub...")
    mcp_tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://api.githubcopilot.com/mcp/",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
            },
        ),
        tool_filter=[
            "search_repositories",
            "search_issues",
            "list_issues",
            "get_issue",
            "list_pull_requests",
            "get_pull_request",
        ],
    )

    print("Initializing native Github Agent...")
    tools = await mcp_tools.get_tools()
    agent = Agent(
        name="Github_Agent",
        instruction=(
            "You are a specialized assistant for interacting with GitHub. "
            "Use the provided tools to search for repositories, find issues, "
            "and retrieve pull request information. Respond with the "
            "information you find."
        ),
        tools=tools,
        model=os.getenv("MAIN_MODEL", "gemini-1.5-flash-001"),
    )
    return agent


def get_agent_for_deployment() -> Agent:
    """
    --- NEW DEPLOYMENT FUNCTION ---
    Synchronous wrapper to create and return the agent for deployment.
    This is intended to be called from a standard Python script.
    """
    print("Creating GitHub agent for deployment...")
    # asyncio.run() creates a new event loop to run our async creator function.
    return asyncio.run(_get_agent_async())


class GithubAgentExecutor(AgentExecutor):
    """
    An AgentExecutor that runs a native ADK Agent and translates
    its output for the A2A protocol.
    """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.agent: Agent | None = None

    @classmethod
    async def create(cls):
        """Asynchronously creates and initializes an instance of GithubAgentExecutor."""
        executor = cls()
        print("Executor: Initializing native Github Agent...")
        # The creation logic is now synchronous.
        executor.agent = await _get_agent_async()
        return executor

    def _run_agent_sync(self, runner: Runner, content: types.Content, user_id: str, session_id: str) -> str:
        """A synchronous helper to run the agent's blocking execution loop."""
        final_message = ""
        print("Executing synchronous agent run in a separate thread.")
        for event in runner.run(new_message=content, user_id=user_id, session_id=session_id):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            final_message += part.text
        print("Synchronous agent run finished.")
        return final_message

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """This method now runs the agent with a timeout."""
        if not self.agent:
            raise ServerError(error=InternalError("Agent not initialized."))

        query = context.get_user_input()
        if not query:
            raise ServerError(error=InvalidParamsError("User query cannot be empty."))

        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            print(f"Running Github Agent with query: '{query}'")
            session_service = InMemorySessionService()
            app_name = "github_agent_app"
            session_id = "1234"
            user_id = "user1234"
            await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
            runner = Runner(agent=self.agent, app_name=app_name, session_service=session_service)
            content = types.Content(role="user", parts=[types.Part(text=query)])
            loop = asyncio.get_running_loop()

            try:
                final_message = await asyncio.wait_for(
                    loop.run_in_executor(None, self._run_agent_sync, runner, content, user_id, session_id), timeout=60.0
                )
                if not final_message:
                    final_message = "Agent finished but provided no response."
            except asyncio.TimeoutError:
                print("Agent execution timed out.")
                final_message = "The agent took too long to respond. Please try a more specific query."

            await updater.add_artifact([Part(root=TextPart(text=final_message))], name="github_result")
            await updater.complete()
        except Exception as e:
            print(f"An error occurred during execution: {e}", exc_info=True)
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())


@click.command()
@click.option("--host", default="localhost", help="The host to run the server on.")
@click.option("--port", default=8002, help="The port to run the server on.")
def main(host: str, port: int):
    """Starts the Github Agent A2A server."""

    async def start_server():
        print("Defining Agent Card...")
        agent_card = AgentCard(
            name="GithubAgent-A2A",
            description="An agent that uses MCP to interact with GitHub.",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            default_input_modes=GithubAgentExecutor.SUPPORTED_CONTENT_TYPES,
            default_output_modes=GithubAgentExecutor.SUPPORTED_CONTENT_TYPES,
            capabilities=AgentCapabilities(streaming=False),
            skills=[
                AgentSkill(
                    id="query_github",
                    name="Query GitHub",
                    description="Takes a natural language query about GitHub issues, PRs, or repos and returns an answer.",
                    tags=["github", "mcp", "issues", "repositories", "pull requests"],
                    examples=['Find issues related to "authentication" in the "google/adk-python" repository.'],
                )
            ],
        )

        try:
            agent_executor = await GithubAgentExecutor.create()
            request_handler = DefaultRequestHandler(agent_executor=agent_executor, task_store=InMemoryTaskStore())
            server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
            print(f"Starting Github Agent A2A server at http://{host}:{port}")
            config = uvicorn.Config(server.build(), host=host, port=port)
            server_instance = uvicorn.Server(config)
            await server_instance.serve()

        except Exception as e:
            print(f"Failed to start server: {e}", exc_info=True)

    asyncio.run(start_server())


if __name__ == "__main__":
    main()
