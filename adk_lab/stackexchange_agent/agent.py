# file: stackexchange_agent/agent.py

import logging
from typing import Annotated, Any

from langchain_community.tools import StackExchangeTool
from langchain_community.utilities import StackExchangeAPIWrapper
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


# --- No changes to your State definition ---
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class StackExchangeAgent:
    """A self-contained agent that searches Stack Exchange."""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.graph = self._create_graph()
        self.tool = StackExchangeTool(api_wrapper=StackExchangeAPIWrapper())

    def _create_graph(self):
        """Creates the LangGraph agent."""
        graph = StateGraph(AgentState)
        graph.add_node("agent", self._call_model)
        graph.set_entry_point("agent")
        graph.set_finish_point("agent")
        return graph.compile()

    def _call_model(self, state: AgentState) -> dict[str, Any]:
        """The primary node for the agent's logic."""
        try:
            messages = state.get("messages", [])
            if not messages:
                logging.error("Agent received a state with no messages.")
                return {"messages": [SystemMessage(content="Error: No input query was provided.")]}

            query = messages[-1].content
            # tool_result = search_stack_exchange.invoke({"query": query})
            logging.info(f"--- Searching StackExchange for: {query} ---")
            tool_result = self.tool.invoke(query)
            return {"messages": [SystemMessage(content=tool_result)]}

        except Exception as e:
            logging.exception(f"An error occurred in the agent node: {e}")
            return {"messages": [SystemMessage(content=f"An internal error occurred: {e}")]}

    def invoke(self, query: str, context_id: str) -> dict[str, Any]:
        """
        Executes the agent and returns a final dictionary.
        This is what the A2A Executor will call.
        """
        inputs = {"messages": [("user", query)]}
        # Note: Your simple agent doesn't use conversation history (checkpointer),
        # so context_id is not used here, but it's good practice to include it.
        final_state = self.graph.invoke(inputs)

        last_message = final_state["messages"][-1]

        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": last_message.content,
        }
