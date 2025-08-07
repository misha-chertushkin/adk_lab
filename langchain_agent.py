from fastapi import FastAPI
from langserve import add_routes
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langchain_core.tools import tool


# 1. Define your tool (replace with your actual StackExchange API logic)
@tool
def search_stack_exchange(query: str) -> str:
    """Searches StackExchange for the given query."""
    # In a real implementation, you would use httpx or requests
    # to call the StackExchange API.
    print(f"--- Searching StackExchange for: {query} ---")
    return f"Found 3 results for '{query}'. The top answer suggests correcting the endpoint URL."


# 2. Define the State for your LangGraph Agent
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# 3. Define the nodes of the graph
def call_model(state: AgentState):
    """The primary node for the agent's logic."""
    query = state["messages"][-1].content
    tool_result = search_stack_exchange.invoke({"query": query})
    # We will return the result directly as a SystemMessage
    return {"messages": [SystemMessage(content=tool_result)]}


# 4. Assemble the LangGraph
graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.set_entry_point("agent")
graph.set_finish_point("agent")
runnable_agent = graph.compile()

# 5. Create the FastAPI App and expose the agent with LangServe
app = FastAPI(
    title="StackExchange LangChain Server",
    version="1.0",
    description="A server exposing a StackExchange agent built with LangGraph.",
)

# This exposes your agent at the `/stackexchange` endpoint
add_routes(
    app,
    runnable_agent,
    path="/stackexchange",
)

# To run this server: uvicorn stackexchange_agent.main:app --reload --port 8001
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
