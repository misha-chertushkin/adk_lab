# file: stackexchange_agent/main.py

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from adk_lab.stackexchange_agent.agent import StackExchangeAgent
from adk_lab.stackexchange_agent.agent_executor import StackExchangeExecutor


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=8001)
def main(host, port):
    """Starts the StackExchange Agent A2A server."""

    # Define the formal AgentCard
    agent_card = AgentCard(
        name="StackExchangeAgent-A2A",
        description="Agent specialized in searching Stack Exchange via the A2A protocol.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        default_input_modes=StackExchangeAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=StackExchangeAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id='search_stackexchange',
                name='Search Stack Exchange',
                description='Takes a user query and returns a single, complete answer from Stack Exchange.',
                # --- THIS LINE IS THE FIX ---
                tags=['search', 'stackexchange', 'errors', 'debugging'],
                examples=['How do I fix a 500 Internal Server Error in FastAPI?']
            )
        ],
    )

    # Assemble the A2A server components
    request_handler = DefaultRequestHandler(
        agent_executor=StackExchangeExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()
