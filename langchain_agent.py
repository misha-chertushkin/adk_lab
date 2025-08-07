# file: stackexchange_agent/main.py

from fastapi import FastAPI
from langserve import add_routes
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
import logging

# --- No changes to your tool definition ---
@tool
def search_stack_exchange(query: str) -> str:
    """Searches StackExchange for the given query."""
    print(f"--- Searching StackExchange for: {query} ---")
    return f"Found 3 results for '{query}'. The top answer suggests correcting the endpoint URL."

# --- No changes to your State definition ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# --- MODIFIED: Add error handling to your agent node ---
def call_model(state: AgentState):
    """The primary node for the agent's logic, now with error handling."""
    try:
        # Use .get() for safer dictionary access
        messages = state.get("messages", [])
        
        # Check if there are any messages to process
        if not messages:
            logging.error("Agent received a state with no messages.")
            return {"messages": [SystemMessage(content="Error: No input query was provided to the agent.")]}
            
        # Get the content from the last message
        query = messages[-1].content
        tool_result = search_stack_exchange.invoke({"query": query})
        return {"messages": [SystemMessage(content=tool_result)]}

    except Exception as e:
        # Log the full exception and return a helpful error message
        logging.exception(f"An error occurred in the agent node: {e}")
        return {"messages": [SystemMessage(content=f"An internal error occurred: {e}")]}


# --- No changes to the rest of the file ---
graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.set_entry_point("agent")
graph.set_finish_point("agent")
runnable_agent = graph.compile()

app = FastAPI(
  title="StackExchange LangChain Server",
  version="1.0",
  description="A server exposing a StackExchange agent built with LangGraph.",
)

add_routes(
    app,
    runnable_agent,
    path="/stackexchange",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)