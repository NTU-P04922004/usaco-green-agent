import asyncio
import json
import os
from uuid import uuid4

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientConfig,
    ClientFactory,
)
from a2a.types import Message, Role, TextPart, TransportProtocol
from loguru import logger

logger.remove()
log_file_path = "logs/client.log"
if os.path.exists(log_file_path):
    with open(log_file_path, "w") as f:
        f.truncate(0)  # Erase all contents
logger.add(log_file_path)


async def main():
    base_url = "http://usaco-green-agent:9009"
    async with httpx.AsyncClient(timeout=120) as httpx_client:
        # Initialize A2ACardResolver
        # agent_card_path uses default, extended_agent_card_path also uses default
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )

        # Fetches from default public path
        public_card = await resolver.get_agent_card()

        config = ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[
                TransportProtocol.jsonrpc,
                TransportProtocol.http_json,
            ],
            use_client_preference=True,
            streaming=False,
        )
        factory = ClientFactory(config)
        client = factory.create(public_card)

        payload = {
            "participants": {"agent": "http://usaco-purple-agent:9009"},
            "config": {
                "problem_ids": ["259_bronze_cow_race", "396_bronze_secret_code"]
            },
        }
        msg = Message(
            role=Role.user,
            parts=[TextPart(text=json.dumps(payload))],
            message_id=str(uuid4()),
        )

        async for response in client.send_message(msg):
            task, _ = response
            response_data = task.model_dump(mode="json", exclude_none=True)
            logger.debug(f"Server response:\n{json.dumps(response_data, indent=2)}")

            if response_data["status"]["state"] == "completed":
                for part in response_data["artifacts"][0]["parts"]:
                    if part.get("text", None):
                        text = part["text"]
                    else:
                        text = json.dumps(part["data"])
                    message = f"Agent: {text}"
                    print(message)
                    logger.info(message)
            else:
                message = (
                    f"Agent: {response_data['status']['message']['parts'][0]['text']}"
                )
                print(message)
                logger.info(message)


if __name__ == "__main__":
    asyncio.run(main())
