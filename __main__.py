import asyncio

import dotenv
import os
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import google.auth
import vertexai


# Use a relative import to get the agent from the same package
from .agent_v2 import code_assist_agent

APP_NAME = "code_assist_app"
USER_ID = "user1234"
SESSION_ID = "1234"

async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=code_assist_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

async def call_agent_async(query: str):
    """
    Sets up the runner, calls the agent with a query, and prints the interaction.
    """
    session_service = InMemorySessionService()
    runner = Runner(
        agent=code_assist_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    print(f"User Query: {query}\n")

    content = types.Content(role="user", parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    events = runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    )

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("\nAgent Response:", final_response)


def main():
    """Main entry point for running the agent from the command line."""
    dotenv.load_dotenv()
    application_default_credentials, _ = google.auth.default()
    vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location=os.getenv("GOOGLE_CLOUD_LOCATION"))
    initial_query = "I'm getting a 'NullPointerException' in the user authentication module. Can you help me with that?"
    # initial_query = "In C++ what is the int size?"
    asyncio.run(call_agent_async(initial_query))


if __name__ == "__main__":
    main()