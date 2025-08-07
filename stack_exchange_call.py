import httpx
from google.adk.tools import FunctionTool


async def call_stackexchange_agent(query: str) -> str:
    """
    Calls the external StackExchange agent to find solutions for a technical query.
    """
    agent_server_url = "http://localhost:8001/stackexchange/invoke"
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "input": {
                    "messages": [
                        # THE FIX: Change "type": "user" to "type": "human"
                        {"type": "human", "content": query}
                    ]
                }
            }
            
            response = await client.post(agent_server_url, json=payload, timeout=45.0)
            response.raise_for_status() 
            
            result = response.json()
            final_message = result.get("output", {}).get("messages", [])[-1]
            
            if isinstance(final_message, dict):
                 return f"Response from StackExchange Agent: {final_message.get('content', 'No content found.')}"
            return "Received an unexpected response format from the StackExchange Agent."

        except httpx.RequestError as e:
            return f"Network error calling StackExchange Agent: {e}"
        except Exception as e:
            return f"An unexpected error occurred while calling the StackExchange Agent: {e}"
        
stackexchange_agent = FunctionTool(func=call_stackexchange_agent)