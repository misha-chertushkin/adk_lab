from google.adk.agents import Agent
from google.adk.tools import google_search
import os
import dotenv

dotenv.load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")  # Replace with your actual key

# os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# root_agent = Agent(
#     name="search_assistant",
#     model="gemini-2.0-flash", # Or your preferred Gemini model
#     instruction="You are a helpful assistant. Answer user questions using Google Search when needed.",
#     description="An assistant that can search the web.",
#     tools=[google_search]
# )

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

import asyncio
from google.genai import types

# Agent Definition
AGENT_NAME = "bigquery_agent"
APP_NAME = "bigquery_app"
USER_ID = "user1234"
SESSION_ID = "1234"
GEMINI_MODEL = "gemini-2.0-flash"
# root_agent = Agent(
#     model=GEMINI_MODEL,
#     name=AGENT_NAME,
#     description=(
#         "Agent to answer questions about BigQuery data and models and execute"
#         " SQL queries."
#     ),
#     instruction="""\
#         You are a data science agent with access to several BigQuery tools.
#         Make use of those tools to answer the user's questions.
#     """,
#     tools=[bigquery_toolset],
# )


# # Agent Interaction
# def call_agent(query):
#     """
#     Helper function to call the agent with a query.
#     """
#     content = types.Content(role='user', parts=[types.Part(text=query)])
#     events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

#     print("USER:", query)
#     for event in events:
#         if event.is_final_response():
#             final_response = event.content.parts[0].text
#             print("AGENT:", final_response)

# call_agent("Are there any ml datasets in bigquery-public-data project?")
# call_agent("Tell me more about ml_datasets.")
# call_agent("Which all tables does it have?")
# call_agent("Tell me more about the census_adult_income table.")
# call_agent("How many rows are there per income bracket?")




from google.adk.agents import Agent
# --- Tool Definitions ---


# 2. CodeManualTool (Vertex AI Search) - Placeholder
# Assuming a similar structure for a Vertex AI Search tool
# from google.adk.tools.vertexai_search import VertexAISearchToolset # Fictional import
# code_manual_tool = VertexAISearchToolset(
#     name="CodeManualTool",
#     description="A tool to search through the codebase documentation and manuals stored in Vertex AI Search. Use this to understand how different parts of the code work.",
#     # configuration would go here
# )

# 3. ErrorStorageTool (Google Drive) - Placeholder
# Assuming a similar structure for a Google Drive tool
# from google.adk.tools.google_drive import GoogleDriveToolset # Fictional import
# error_storage_tool = GoogleDriveToolset(
#     name="ErrorStorageTool",
#     description="A tool to access error logs and images stored in Google Drive. Use this to get more context on user-reported errors.",
#     # configuration would go here
# )


# 3. Code Assist Agent (The main agent)
code_assist_agent = Agent(
    name="CodeAssistAgent",
    model="gemini-2.0-flash",
    description="The main agent that assists users with code-related issues. It can use various tools and other agents to resolve problems.",
    instruction="""You are a Code Assistant. Your goal is to help users resolve their coding issues.
    You have access to a set of tools and other specialized agents.
    When a user provides an error message or a description of a problem, you should:
    1. Use the ErrorStorageTool to look for any associated images or logs.
    2. Use the BugDatabaseTool to check if it's a known bug.
    3. Use the CodeManualTool to search for relevant documentation.
    4. If the issue is not in the bug database or documentation, you can consult the GithubAgent to check the code or the StackExchangeAgent to look for solutions online.
    5. Finally, provide a blended response to the user with your findings and a suggested solution.
    """,
    tools=[
        bigquery_toolset,
        # code_manual_tool,
        # error_storage_tool,
        # github_agent_tool,
        # stackexchange_agent_tool
    ]
)

# --- Runner Setup (for demonstration) ---
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio

# This part is for demonstrating how to run the agent.
# In a real multi-agent system, this would be handled by Agentspace.
if __name__ == "__main__":
    # Session and Runner
    session_service = InMemorySessionService()
    session = asyncio.run(session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID))
    runner = Runner(agent=code_assist_agent, app_name=APP_NAME, session_service=session_service)

    async def main():
        session = await session_service.create_session(app_name="adk_lab")
        query = "I'm getting a 'NullPointerException' in the user authentication module. Can you help me with that?"
        print(f"User: {query}")

        events = runner.run(session_id=session.session_id, new_message=types.Content(parts=[types.Part(text=query)]))
        async for event in events:
            if event.is_final_response():
                print(f"Agent: {event.content.parts[0].text}")

    asyncio.run(main())
