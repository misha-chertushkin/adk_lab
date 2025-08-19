import asyncio
from uuid import uuid4

import httpx

# Correct imports for the modern a2a-sdk
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest, TextPart
from google.adk.tools import FunctionTool

# The URL of your new A2A-compliant agent
# STACKEXCHANGE_AGENT_URL = "http://localhost:8001/"
# STACKEXCHANGE_AGENT_URL = "https://stackexchange-agent-wbkml5x37q-uc.a.run.app/"
from adk_lab.utils.proxy import STACKEXCHANGE_AGENT_URL


async def call_stackexchange_a2a(query: str) -> str:
    """
    Discovers and invokes the StackExchange A2A agent using the modern A2A SDK.
    """
    try:
        async with httpx.AsyncClient() as httpx_client:
            # Step 1: Discover the agent using the A2ACardResolver
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=STACKEXCHANGE_AGENT_URL)
            agent_card = await resolver.get_agent_card()
            # Step 2: Initialize the A2AClient with the resolved card
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card, url=STACKEXCHANGE_AGENT_URL)
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
            # The actual task is in the 'result' field of the response object
            final_task = response_object

            # Step 5: Process the response artifacts from the final task object
            if final_task and final_task.root and final_task.root.result and final_task.root.result.artifacts:
                # The result is in the artifacts list, as defined in our executor
                artifact_content = final_task.root.result.artifacts[0].parts[0].root.text
                return f"Response from StackExchange A2A Agent: {artifact_content}"
            else:
                return f"StackExchange A2A Agent returned no result. Final status: {final_task.status if final_task else 'Unknown'}"

    except Exception as e:
        print("NOOOOOOO: StackExchange A2A Agent did not return a result. Possible cause:")
        print(e)

        return f"An error occurred while communicating with the StackExchange A2A Agent: {e}"


# The FunctionTool definition remains the same, it just wraps the updated function
stackexchange_agent = FunctionTool(
    func=call_stackexchange_a2a,
)
