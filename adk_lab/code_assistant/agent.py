import os

import dotenv
import google.auth
import vertexai
from google.adk.agents import Agent
from google.adk.tools import load_artifacts

from adk_lab.github_call import github_agent
from adk_lab.stack_exchange_call import stackexchange_agent
from adk_lab.tools import bug_database_tool, code_manual_tool, gdrive_upload_tool

dotenv.load_dotenv()
application_default_credentials, _ = google.auth.default()
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION"),
    credentials=application_default_credentials,
)

root_agent = Agent(
    name="code_assist_agent",
    model=os.getenv("MAIN_MODEL", "gemini-2.5-pro"),
    instruction=(
        "You are a 'Code Assist Agent'. Your goal is to help users debug code errors. "
        "You have 6 tools available:\n"
        "1. bug_database_tool: To search a BigQuery database of known bugs.\n"
        "2. code_manual_tool: To search documentation using Vertex AI Search.\n"
        "3. stackexchange_agent: To retrieve error logs from Stack Exchange.\n"
        "4. github_agent: To ask about pull requests, github repositories and issues.\n"
        "5. gdrive_upload_tool: To save an image of a bug or screenshot to Google Drive for documentation.\n\n"
        "6. load_artifacts: To obtain the content of the uploaded file if if exists (txt or image)"
        "If there is an uploaded file use the `load_artifacts` tool to load the content of the uploaded file, also you must use you must use the `gdrive_upload_tool` tool to save it."
        "Analyze the user's query"
        "Then, invoke the other relevant tools to find a solution. "
        "In case you find something useful, print it back to the user. "
        "Do not ask any follow-up questions; just provide the best helpful answer. "
        "When outputing final answer explicitly say from which tool which relevant information was obtained. "
    ),
    description="An agent that helps developers fix bugs by searching databases, manuals, and storage.",
    tools=[
        bug_database_tool,
        code_manual_tool,
        stackexchange_agent,
        github_agent,
        gdrive_upload_tool,
        load_artifacts,
    ],
)
