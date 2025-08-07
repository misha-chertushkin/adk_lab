import os

from google.adk.agents import Agent
import dotenv

from .tools import bug_database_tool, code_manual_tool, error_storage_tool
dotenv.load_dotenv()

# --- 1. Environment Setup ---
# It's good practice to ensure the API key is set.
# In a real application, use a secure method to manage keys.
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")  # Replace with your actual key

# --- 2. Tool Definitions ---
# Here we define the custom tools for our Code Assist Agent.

code_assist_agent = Agent(
    name="code_assist_agent",
    model=os.getenv("MAIN_MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a 'Code Assist Agent'. Your goal is to help users debug code errors. "
        "You have three tools available:\n"
        "1. bug_database_tool: To search a BigQuery database of known bugs.\n"
        "2. code_manual_tool: To search documentation using Vertex AI Search.\n"
        "3. error_storage_tool: To retrieve error logs from Google Drive.\n"
        "Analyze the user's query and decide which tool is the most appropriate to use. "
        "If the tools don't provide a sufficient answer, you will later have the option to escalate to other agents."
        "In case you find something useful, print it back to user"
        "Do not ask any follow-up questions, just give the best helpful answer to user back"
    ),
    description="An agent that helps developers fix bugs by searching databases, manuals, and storage.",
    tools=[bug_database_tool, code_manual_tool, error_storage_tool],
)
