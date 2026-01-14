import json
import time
from typing import Any

from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Message, Part, TaskState, TextPart
from a2a.utils import get_message_text, new_agent_text_message
from judge import Judge, get_problem_path
from pydantic import BaseModel, HttpUrl, ValidationError

from loguru import logger
from messenger import Messenger


class EvalRequest(BaseModel):
    """Request format sent by the AgentBeats platform to green agents."""

    participants: dict[str, HttpUrl]  # role -> agent URL
    config: dict[str, Any]


class Agent:
    # Fill in: list of required participant roles, e.g. ["pro_debater", "con_debater"]
    required_roles: list[str] = []
    # Fill in: list of required config keys, e.g. ["topic", "num_rounds"]
    required_config_keys: list[str] = []

    def __init__(self):
        self.messenger = Messenger()
        # Initialize other state here

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        missing_roles = set(self.required_roles) - set(request.participants.keys())
        if missing_roles:
            return False, f"Missing roles: {missing_roles}"

        missing_config_keys = set(self.required_config_keys) - set(
            request.config.keys()
        )
        if missing_config_keys:
            return False, f"Missing config keys: {missing_config_keys}"

        # Add additional request validation here

        return True, "ok"

    async def run(self, message: Message, updater: TaskUpdater) -> None:
        """Implement your agent logic here.

        Args:
            message: The incoming message
            updater: Report progress (update_status) and results (add_artifact)

        Use self.messenger.talk_to_agent(message, url) to call other agents.
        """
        input_text = get_message_text(message)

        try:
            request: EvalRequest = EvalRequest.model_validate_json(input_text)
            ok, msg = self.validate_request(request)
            if not ok:
                await updater.reject(new_agent_text_message(msg))
                return
        except ValidationError as e:
            logger.exception(e)
            await updater.reject(new_agent_text_message(f"Invalid request: {e}"))
            return

        # Use request.participants to get participant agent URLs by role
        # Use request.config for assessment parameters

        logger.info(f"Starting evaluation: {request}")
        start_time = time.time()

        problem_ids = request.config.get("problem_ids", None)
        participant_id = "agent"
        purple_agent_url = str(request.participants[participant_id])

        logger.info(f"Running {len(problem_ids)} tasks")
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"Starting evaluation of {len(problem_ids)} tasks"),
        )

        metrics: dict[str, Any] = {"pass_1": 0, "time": 0, "tasks": {}}

        try:
            for problem_id in problem_ids:
                logger.info(f"Running task {problem_id}...")
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(f"Running task {problem_id}..."),
                )

                try:
                    problem_id = problem_id
                    judge = Judge(get_problem_path(problem_id))
                    problem_description = judge.get_problem_description()

                    response = await self.messenger.talk_to_agent(
                        problem_description, purple_agent_url, new_conversation=False
                    )
                    logger.info(f"Participant {participant_id} response:\n{response}")

                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message("Starting evaluation."),
                    )
                    logger.info("Starting evaluation.")

                    result = judge.run_all_tests(response)

                    logger.info(f"Evaluation result: {result}")

                    metrics["tasks"][problem_id] = result.verdict
                except Exception as e:
                    logger.error(f"Task {problem_id} failed: {e}", exc_info=True)
                    metrics["tasks"][problem_id] = "Error"

            time_used = time.time() - start_time
            metrics["time"] = time_used
            accepted = total = 0
            for pid, result in metrics["tasks"].items():
                total += 1
                if result == "Accepted":
                    accepted += 1
            metrics["pass_1"] = accepted / total

            await updater.add_artifact(
                parts=[
                    Part(root=TextPart(text="Evaluation completed!")),
                    Part(root=DataPart(data=metrics)),
                ],
                name="Result",
            )
        except Exception as e:
            logger.error(f"Evalution failed: {e}", exc_info=True)
            await updater.reject(new_agent_text_message(f"Evalution failed: {e}"))
