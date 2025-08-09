# file: adk_lab/stackexchange_agent/main.py

import os
import uvicorn
import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

# Make sure the imports point to your project structure
from adk_lab.stackexchange_agent.agent import StackExchangeAgent
from adk_lab.stackexchange_agent.agent_executor import StackExchangeExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Starts the StackExchange Agent A2A server, configured for Cloud Run."""
    
    # Read port from environment variable, default to 8080 for local testing
    port = int(os.environ.get("PORT", 8080))
    # In a container, listen on all interfaces
    public_url = os.environ.get('AGENT_PUBLIC_URL', f'http://localhost:{port}/')
    
    logger.info(f"Using public URL for Agent Card: {public_url}")

    logger.info("Defining Agent Card...")
    # The URL will be dynamically provided by Cloud Run,
    # so we use a placeholder or leave it generic.
    # A controller service would typically update this upon discovery.
    agent_card = AgentCard(
        name="StackExchangeAgent-A2A",
        description="Agent specialized in searching Stack Exchange via the A2A protocol.",
        url=public_url,  #, f"/", # Use a relative URL for simplicity
        version="1.0.0",
        default_input_modes=StackExchangeAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=StackExchangeAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id='search_stackexchange',
                name='Search Stack Exchange',
                description='Takes a user query and returns a single, complete answer from Stack Exchange.',
                tags=['search', 'stackexchange', 'errors', 'debugging'],
                examples=['How do I fix a 500 Internal Server Error in FastAPI?']
            )
        ],
    )

    # Assemble the A2A server components
    logger.info("Initializing A2A request handler...")
    request_handler = DefaultRequestHandler(
        agent_executor=StackExchangeExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

    # The server still listens on 0.0.0.0 inside the container
    listen_host = "0.0.0.0"
    server = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

    logger.info(f"Starting Uvicorn server on {listen_host}:{port}")
    uvicorn.run(server.build(), host=listen_host, port=port)


if __name__ == "__main__":
    main()