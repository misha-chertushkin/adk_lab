import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

# --- MODIFIED: Add UnsupportedOperationError to imports ---
from a2a.types import InternalError, InvalidParamsError, Part, TextPart, UnsupportedOperationError
from a2a.utils import new_task
from a2a.utils.errors import ServerError

from adk_lab.stackexchange_agent.agent import StackExchangeAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StackExchangeExecutor(AgentExecutor):
    """The Bridge between the A2A server and the StackExchangeAgent."""

    def __init__(self):
        self.agent = StackExchangeAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handles an incoming A2A request."""
        query = context.get_user_input()
        if not query:
            raise ServerError(error=InvalidParamsError("User query cannot be empty."))

        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            result = self.agent.invoke(query, task.context_id)
            await updater.add_artifact(
                [Part(root=TextPart(text=result["content"]))],
                name="stackexchange_result",
            )
            await updater.complete()

        except Exception as e:
            logger.error(f"An error occurred during agent execution: {e}")
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handles a request to cancel the task."""
        # Since this agent completes its task very quickly, cancellation is not supported.
        raise ServerError(error=UnsupportedOperationError())
