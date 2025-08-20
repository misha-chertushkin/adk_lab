# adk_lab/deployment/deploy_code_assistant.py

import os
import sys

import vertexai
from vertexai.preview import reasoning_engines

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "chertushkin-genai-sa")
LOCATION = "us-central1"
STAGING_BUCKET_URI = "gs://deploy-staging-bucket"

# --- Agent and Requirements Path ---
# This assumes the script is run from the root of the `adk_lab` project directory.
REQUIREMENTS_PATH = "requirements.txt"

# This ensures the 'adk_lab' directory is on the Python path
# to allow for the agent import.
sys.path.append(os.getcwd())

try:
    from adk_lab.code_assistant.agent import root_agent as code_assistant_agent
except ImportError as e:
    print(f"🚨 Error importing the agent: {e}")
    print(
        "Please ensure this script is run from your project's root directory (the one containing the 'adk_lab' folder)."
    )
    exit(1)


def read_requirements(path):
    """Reads a requirements.txt file and returns a list of packages."""
    if not os.path.exists(path):
        print(f"🚨 Error: Requirements file not found at '{path}'")
        print("Please create the file and add your agent's dependencies.")
        return []
    with open(path) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def deploy_agent():
    """
    Deploys the Code Assistant agent to Google Cloud's Agent Engine,
    following the official documentation.
    """
    print(f"Starting deployment for project '{PROJECT_ID}' in '{LOCATION}'...")

    # 1. Initialize the Vertex AI SDK
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET_URI)

    # 2. Read agent dependencies
    requirements = read_requirements(REQUIREMENTS_PATH)
    if not requirements:
        print("Deployment aborted due to missing requirements.")
        return

    print(f"Found {len(requirements)} packages in '{REQUIREMENTS_PATH}'.")

    # 3. Prepare the agent for deployment using the correct AdkApp wrapper
    # As per the documentation, AdkApp is accessed via reasoning_engines.
    app_for_deployment = reasoning_engines.AdkApp(
        agent=code_assistant_agent,
        enable_tracing=True,
    )

    print("Deploying the agent to Agent Engine... This may take several minutes. ⏳")

    # 4. Deploy the agent using ReasoningEngine.create()
    # This is the correct method for creating a new deployment.
    deployed_agent = reasoning_engines.ReasoningEngine.create(
        app_for_deployment,
        display_name="Code Assistant Agent",
        requirements=requirements,
        # This tells Agent Engine to install your local 'adk_lab' package.
        # It looks for a pyproject.toml or setup.py in the specified directory.
        extra_packages=["."],
    )

    print("\n🚀 Deployment successful! 🚀\n")
    print(f"Agent Display Name: {deployed_agent.display_name}")
    print(f"Agent Resource Name: {deployed_agent.resource_name}")
    print("You can now interact with your deployed agent using its resource name.")


if __name__ == "__main__":
    if PROJECT_ID == "your-gcp-project-id" or STAGING_BUCKET_URI == "gs://your-gcs-bucket-for-staging":
        print("🚨 Configuration Error: Please update PROJECT_ID and STAGING_BUCKET_URI at the top of the script.")
    else:
        deploy_agent()
