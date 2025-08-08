def list_secrets(project_id: str) -> None:
    """
    List all secrets in the given project.
    """

    # Import the Secret Manager client library.
    from google.cloud import secretmanager

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the parent project.
    parent = f"projects/{project_id}"

    # List all secrets.
    for secret in client.list_secrets(request={"parent": parent}):
        print(f"Found secret: {secret.name}")

list_secrets("chertushkin-genai-sa")


# adk_lab/deployment/test_deployed_agent.py
# This script does not work, dont use
import vertexai
from vertexai.preview import reasoning_engines

# --- Configuration ---
# Details extracted from your query URL
PROJECT_ID = "chertushkin-genai-sa"
LOCATION = "us-central1"
REASONING_ENGINE_ID = "102659201662189568"
# adk_lab/deployment/test_deployed_agent.py

import vertexai
from vertexai.preview import reasoning_engines
import asyncio

# --- Configuration ---
# Details extracted from your query URL
PROJECT_ID = "chertushkin-genai-sa"
LOCATION = "us-central1"
REASONING_ENGINE_ID = "102659201662189568"

async def query_agent_with_session():
    """
    Initializes a remote agent, creates a session, and sends a query.
    """
    session = None
    try:
        print("Connecting to the deployed agent...")
        # 1. Initialize the Vertex AI SDK
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # 2. Get a reference to the remote reasoning engine
        remote_agent = reasoning_engines.ReasoningEngine(REASONING_ENGINE_ID)
        print(dir(remote_agent))
        # 3. Create a new session for the conversation
        print("Creating a new session...")
        session_info = remote_agent.create_session(user_id='user1234')
        session_id = session_info.get('id')
        
        if not session_id:
            raise ValueError("Failed to create a session or retrieve session ID.")

        print(f"✅ Session created: {session_id}")

        # 4. Send a query by calling the agent object itself, passing the session_id
        # and the other input arguments.
        print("Sending query to the session...")
        response = await remote_agent(
            input="How do I write a function in Python to reverse a string?",
            session_id=session_id
        )

        print("\n✅ Agent Response: \n")
        print(response)

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    # Run the async function using asyncio.
    asyncio.run(query_agent_with_session())


# curl -X POST \
#     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
#     -H "Content-Type: application/json" \
#     "https://us-central1-aiplatform.googleapis.com/v1/projects/chertushkin-genai-sa/locations/us-central1/reasoningEngines/102659201662189568:query" \
#     -d '{
#               "parts": [{"text": "How do I write a function in Python to reverse a string?"}],
#               "role": "human"
#         }'