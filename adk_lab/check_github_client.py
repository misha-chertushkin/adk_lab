import asyncio
import logging
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest
from a2a.utils.constants import (AGENT_CARD_WELL_KNOWN_PATH,
                                 EXTENDED_AGENT_CARD_PATH)

from adk_lab.utils.proxy import logger, GITHUB_AGENT_URL


async def main() -> None:

    # remote testing
    base_url = GITHUB_AGENT_URL
    # uncomment for local testing
    # base_url = 'http://localhost:8080'

    # ✨ FIX 1: Increase the HTTP client timeout ✨
    # The default is 5 seconds, which is too short for the agent.
    timeout = httpx.Timeout(60.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            logger.info(f"Attempting to fetch public agent card from: {base_url}{AGENT_CARD_WELL_KNOWN_PATH}")
            _public_card = await resolver.get_agent_card()
            logger.info("Successfully fetched public agent card:")
            logger.info(_public_card.model_dump_json(indent=2, exclude_none=True))
            final_agent_card_to_use = _public_card
            logger.info("\nUsing PUBLIC agent card for client initialization (default).")

            if _public_card.supports_authenticated_extended_card:
                try:
                    logger.info(
                        "\nPublic card supports authenticated extended card. "
                        "Attempting to fetch from: "
                        f"{base_url}{EXTENDED_AGENT_CARD_PATH}"
                    )
                    auth_headers_dict = {"Authorization": "Bearer dummy-token-for-extended-card"}
                    _extended_card = await resolver.get_agent_card(
                        relative_card_path=EXTENDED_AGENT_CARD_PATH,
                        http_kwargs={"headers": auth_headers_dict},
                    )
                    logger.info("Successfully fetched authenticated extended agent card:")
                    logger.info(_extended_card.model_dump_json(indent=2, exclude_none=True))
                    final_agent_card_to_use = _extended_card  # Update to use the extended card
                    logger.info("\nUsing AUTHENTICATED EXTENDED agent card for client " "initialization.")
                except Exception as e_extended:
                    logger.warning(
                        f"Failed to fetch extended agent card: {e_extended}. " "Will proceed with public card.",
                        exc_info=True,
                    )
            elif _public_card:  # supports_authenticated_extended_card is False or None
                logger.info("\nPublic card does not indicate support for an extended card. Using public card.")

        except Exception as e:
            logger.error(f"Critical error fetching public agent card: {e}", exc_info=True)
            raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e

        # --8<-- [start:send_message]
        client = A2AClient(httpx_client=httpx_client, agent_card=final_agent_card_to_use, url=base_url)
        logger.info("A2AClient initialized.")

        # ✨ FIX 2: Use a more specific query to test the agent's tools ✨
        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": 'Find issues related to "authentication" in the "google/adk-python" repository.',
                    }
                ],
                "message_id": uuid4().hex,
            },
        }
        request = SendMessageRequest(id=str(uuid4()), params=MessageSendParams(**send_message_payload))

        try:
            print("\n--- Sending first request ---")
            response = await client.send_message(request)
            print(response.model_dump(mode="json", exclude_none=True))
        except httpx.ReadTimeout:
            logger.error("Request timed out. The agent took too long to respond.")


if __name__ == "__main__":
    asyncio.run(main())
