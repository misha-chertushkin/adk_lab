import asyncio
from uuid import uuid4

import httpx
# Correct imports for the modern a2a-sdk
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, TextPart
from google.adk.tools import FunctionTool

# The URL of your new A2A-compliant agent
# GITHUB_AGENT_URL = "https://github-agent-841488258821.us-central1.run.app/"
# GITHUB_AGENT_URL = "https://github-agent-wbkml5x37q-uc.a.run.app/"
# GITHUB_AGENT_URL = "http://localhost:8080/" # Make sure this port matches your server
from adk_lab.utils.proxy import GITHUB_AGENT_URL


async def call_github_a2a(query: str) -> str:
    """
    Discovers and invokes the Github A2A agent using the modern A2A SDK.
    """
    try:
        # Define a longer timeout for the HTTP client. 90 seconds should be plenty.
        timeout = httpx.Timeout(90.0)
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            # Step 1: Discover the agent using the A2ACardResolver
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=GITHUB_AGENT_URL)
            agent_card = await resolver.get_agent_card()

            # Step 2: Initialize the A2AClient with the resolved card
            # The A2AClient will inherit the timeout from the httpx_client it's given
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card, url=GITHUB_AGENT_URL)

            # Step 3: Manually construct the request payload and object
            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(
                    message={
                        "role": "user",
                        "parts": [TextPart(text=query)],
                        "message_id": uuid4().hex,
                    }
                ),
            )

            # Step 4: Send the message. For a non-streaming agent, this returns
            # a SendMessageSuccessResponse object which contains the final task.
            response_object = await client.send_message(request)

            # Step 5: Process the response artifacts from the final task object
            if (
                response_object
                and response_object.root
                and response_object.root.result
                and response_object.root.result.artifacts
            ):
                artifact_content = response_object.root.result.artifacts[0].parts[0].root.text
                return f"Response from Github A2A Agent: {artifact_content}"
            else:
                final_status = response_object.root.status if response_object and response_object.root else "Unknown"
                return f"Github A2A Agent returned no result. Final status: {final_status}"

    except httpx.ReadTimeout:
        # Catch the specific timeout error for a clearer message
        return "Error: The request to the Github A2A Agent timed out. The agent is taking too long to respond."
    except Exception as e:
        print("NOOOOOOO: Github A2A Agent did not return a result. Possible cause:")
        print(e)

        return f"An error occurred while communicating with the Github A2A Agent: {e}"


# The FunctionTool definition remains the same, it just wraps the updated function
github_agent = FunctionTool(
    func=call_github_a2a,
)
