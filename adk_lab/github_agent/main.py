# adk_lab/github_agent/main.py

import asyncio
import os
import uuid

import click
import uvicorn
# --- Manual A2A Server Imports ---
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (AgentCapabilities, AgentCard, AgentSkill, InternalError,
                       InvalidParamsError, Part, TextPart,
                       UnsupportedOperationError)
from a2a.utils import new_task
from a2a.utils.errors import ServerError
from dotenv import load_dotenv
# --- Core ADK/MCP Imports ---
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import (MCPToolset,
                                       StreamableHTTPConnectionParams)
from google.genai import types

from adk_lab.utils.proxy import GITHUB_AGENT_URL, GITHUB_TOKEN

# Load environment variables
load_dotenv()

MCP_URL = "https://api.githubcopilot.com/mcp/"
TOOLS_TO_TEST = ["search_repositories", "search_issues", "list_issues"]


async def _create_agent_with_mcp_tools(mcp_tools: MCPToolset) -> Agent:
    """Creates an ADK Agent using a provided, active MCPToolset instance."""
    print("\n▶️  Fetching tool schemas from MCP...")
    tools = await mcp_tools.get_tools()
    print(f"✅ Success! Fetched {len(tools)} tools.")
    for tool in tools:
        print(f"   - Found tool: {tool.name}")

    agent = Agent(
        name="github_agent",
        model=os.getenv("MAIN_MODEL", "gemini-2.5-pro"),
        description=("Agent to search GitHub events."),
        instruction="You are a specialized assistant for interacting with GitHub. "
        "Use the provided tools to search for repositories, find issues, "
        "and retrieve pull request information. Respond with the "
        "information you find.",
        tools=tools,
    )
    return agent


class GithubAgentExecutor(AgentExecutor):
    """
    An AgentExecutor that runs a native ADK Agent. The entire flow is now
    asynchronous.
    """

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        if not query:
            raise ServerError(error=InvalidParamsError("User query cannot be empty."))

        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        mcp_tools = MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=MCP_URL,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                },
            ),
            tool_filter=TOOLS_TO_TEST,
        )

        try:
            print(f"Running Github Agent with query: '{query}'")
            agent = await _create_agent_with_mcp_tools(mcp_tools)

            session_service = InMemorySessionService()
            app_name = "github_agent_app"
            session_id = str(uuid.uuid4())
            user_id = "user1234"
            await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

            runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
            content = types.Content(role="user", parts=[types.Part(text=query)])

            final_message = ""

            events = runner.run_async(
                new_message=content,
                user_id=user_id,
                session_id=session_id,
            )

            async for event in events:
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if part.text:
                            final_message += part.text

            if not final_message:
                final_message = "Agent finished but provided no response."

            print(f"Agent finished with response: '{final_message[:100]}...'")
            await updater.add_artifact([Part(root=TextPart(text=final_message))], name="github_result")
            await updater.complete()

        except Exception as e:
            print(f"An error occurred during execution: {e}")
            await updater.fail()
            raise ServerError(error=InternalError(str(e))) from e
        finally:
            print("\n▶️  Closing MCP toolset connections...")
            await mcp_tools.close()
            print("✅ Connections closed.")

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())


@click.command()
def main():
    """Starts the Github Agent A2A server, configured for Cloud Run."""

    # For Cloud Run, the server must listen on 0.0.0.0 and use the port
    # specified by the PORT environment variable.
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8080))
    # In a container, listen on all interfaces
    public_url = GITHUB_AGENT_URL
    # uncomment for local testing
    # public_url = f"http://localhost:{port}/")

    async def start_server():
        print("Defining Agent Card...")
        # The agent's public URL is needed for its card so other agents can find it.
        # In a real-world scenario, this might be dynamically discovered.
        agent_card = AgentCard(
            name="GithubAgent-A2A",
            description="An agent that uses MCP to interact with GitHub.",
            url=public_url,
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
            agent_executor = GithubAgentExecutor()
            request_handler = DefaultRequestHandler(agent_executor=agent_executor, task_store=InMemoryTaskStore())
            server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
            print(f"Starting Github Agent A2A server at {public_url}")
            config = uvicorn.Config(server.build(), host=host, port=port)
            server_instance = uvicorn.Server(config)
            await server_instance.serve()
        except Exception as e:
            print(f"Failed to start server: {e}")

    asyncio.run(start_server())


if __name__ == "__main__":
    main()
