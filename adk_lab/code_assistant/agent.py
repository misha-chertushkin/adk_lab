import os

from google.adk.agents import Agent
import dotenv

from adk_lab.tools import bug_database_tool, code_manual_tool, gdrive_upload_tool
from adk_lab.stack_exchange_call import stackexchange_agent
from adk_lab.github_call import github_agent

dotenv.load_dotenv()

root_agent = Agent(
    name="code_assist_agent",
    model=os.getenv("MAIN_MODEL", "gemini-2.5-pro"),
    instruction=(
        "You are a 'Code Assist Agent'. Your goal is to help users debug code errors. "
        "You have four tools available:\n"
        "1. bug_database_tool: To search a BigQuery database of known bugs.\n"
        "2. code_manual_tool: To search documentation using Vertex AI Search.\n"
        "3. stackexchange_agent: To retrieve error logs from Stack Exchange.\n"
        "4. github_agent: To ask about pull reuquest, github repositories and issues.\n"
        "5. gdrive_upload_tool: To save an image of a bug or screenshot to Google Drive for documentation.\n\n"
        "First, analyze the user's query. **If the user provides an image of the error, your first step should be to use the `gdrive_upload_tool` tool to save it.** "
        "Then, invoke the other relevant tools to find a solution. "
        "If the tools don't provide a sufficient answer, you will later have the option to escalate to other agents. "
        "In case you find something useful, print it back to the user. "
        "Do not ask any follow-up questions; just provide the best helpful answer. "
        "Always try to call stackexchange_agent as it contains a lot of useful information."
    ),
    description="An agent that helps developers fix bugs by searching databases, manuals, and storage.",
    tools=[
        bug_database_tool,
        code_manual_tool,
        stackexchange_agent,
        github_agent,
        gdrive_upload_tool,
    ],
)
