import httpx
from google.adk.tools import FunctionTool


async def call_stackexchange_agent(query: str) -> str:
    """
    Calls the external StackExchange agent to find solutions for a technical query.
    Use this when code errors or logic problems could be solved with community-provided answers.
    """
    # The URL points to the LangServe endpoint you created.
    # The '/invoke' path is the standard way to call a LangServe runnable.
    agent_server_url = "http://localhost:8001/stackexchange/invoke"
    
    async with httpx.AsyncClient() as client:
        try:
            # LangServe expects a specific JSON structure for input
            payload = {
                "input": {
                    "messages": [
                        ("user", query) # LangServe understands the ("role", "content") tuple format
                    ]
                }
            }
            
            response = await client.post(agent_server_url, json=payload, timeout=45.0)
            
            # Raise an error for non-2xx responses
            response.raise_for_status() 
            
            # The result from LangServe is nested under 'output' and 'messages'
            result = response.json()
            final_message = result.get("output", {}).get("messages", [])[-1]
            
            # Extract the content from the final message
            if isinstance(final_message, dict):
                 return f"Response from StackExchange Agent: {final_message.get('content', 'No content found.')}"
            return "Received an unexpected response format from the StackExchange Agent."

        except httpx.RequestError as e:
            return f"Network error calling StackExchange Agent: {e}"
        except Exception as e:
            print(e)
            return f"An unexpected error occurred while calling the StackExchange Agent: {e}"
        
stackexchange_agent = FunctionTool(func=call_stackexchange_agent)