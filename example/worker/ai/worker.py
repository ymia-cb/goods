import asyncio
import logging
import os
import socket
from typing import Any

from example.app.schemas.admin.user import CurrentUser
from example.app.services.admin.auth import AuthService
from example.app.services.chat.turn import TurnService
from example.common.config import get_settings
from example.common.event_loop import run_async
from example.infrastucture.db import session_factory
from example.worker.ai.gateway import AIServiceGateway
from example.worker.ai.parse import AIEventParser
from example.worker.ai.results import AIResultService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TurnProcessor:
    def __init__(self):
        self.settings = get_settings()
        self.auth_service = AuthService()
        self.ai_gateway = AIServiceGateway()
        self.event_parser = AIEventParser()

    async def process(self, request_data: dict[str, Any], request_message_id: str):

        access_token = self.auth_service.encode_access_token(CurrentUser(user_id=request_data["user_id"]))
        error:Exception | None = None
        run_id:str | None = None
        run_result:dict[str, Any] | None = None
        try:
            run_id, run_result = await self.run_ai_pipeline(access_token, request_data)
        except Exception as exec:
            error = exec
            logger.exception(f"Error in AI gateway:{request_data["turn_id"]},: {exec}")
        await self._final_modify(run_id, run_result, request_message_id, error)


    async def _final_modify(self, turn_id: str, run_id:str | None, run_result:dict[str, Any] | None, request_message_id: str, error: Exception | None):
        async with session_factory() as session:
            turn_service = TurnService(session)
            result_service = AIResultService(session)
            turn, conversation = await turn_service.find_turn_conversation_by_id(turn_id)
            if turn is not None:
                turn.run_id = run_id
            if conversation.input_revision != turn.snapshot_revision:
                turn_service.mark_superseded(turn)
                await session.commit()
                return
            if error is not None:
                if turn_service.retry_or_fail(turn, error):
                    await session.commit()
                    return
                result_service.save_ai_result(conversation,
                                               turn,
                                               {
                                                   "kind": "error",
                                                   "text": "ai-service处理失败"
                                               })
            else:
                turn_service.mark_superseded(turn)
                if run_result["outcome_type"] == "handoff":
                    await result_service.save_hand_off_result(
                        conversation,
                        turn,
                        run_result
                    )
                else:
                    result_service.save_ai_result(conversation,turn,run_result["content"], message_id=run_result["message_id"])
            conversation.answered_revision = turn.snapshot_revision
            await session.commit()


    async def run_ai_pipeline(self, access_token: str, request_data: dict[str, Any]) -> tuple[str, dict[str, Any | None]  | None]:
        event = await self.ai_gateway.start_run(token=access_token, request=request_data)
        run_id = self.event_parser.find_run_id(event)
        prepared = self.event_parser.has_prepared_decision(event)
        is_need_commit = False
        try:
            if prepared:
                if not await self.validate_before_commit(request_data["turn_id"], run_id):
                    await self.ai_gateway.cancel_run(token=access_token, run_id=run_id)
                    return run_id, None
                event = await self.ai_gateway.commit_run(token=access_token, run_id=run_id, input_revision=request_data["input_revision"])
                is_need_commit = True
            return run_id, self.event_parser.parser_outcome(event)
        except Exception as exec:
            if prepared and not is_need_commit:
                await self.ai_gateway.cancel_run(token=access_token, run_id=run_id)
            raise exec

    async def validate_before_commit(self, turn_id: str, run_id:str) -> bool:
        async with session_factory() as session:
            turn_service = TurnService(session)
            turn_and_conversation = await turn_service.find_turn_conversation_by_id(turn_id)
            turn, conversation = turn_and_conversation
            if run_id :
                turn.run_id = run_id
            if turn.snapshot_revision != conversation.input_revision:
                turn_service.mark_superseded(turn)
                await session.commit()
                return False
            await session.commit()
            return True


class AIWorker:
    def __init__(self):
        self.settings = get_settings()
        self.work_id = f"{socket.gethostname()}:{os.getpid()}"
        self.session_factory = session_factory
        self.turn_processor = TurnProcessor()

    async def start(self):
        while True:
            try:
                process = await self.poll_and_process()

                if not process:
                    await asyncio.sleep(self.settings.ai_worker_poll_interval_ms / 1000)

            except Exception as exec:
                logger.exception(f"Error in AI worker:{self.work_id},: {exec}")

                await asyncio.sleep(1)

    async def poll_and_process(self) -> bool:
        await self._recover_expired_turns()
        claimed_turn = await self.claimed_turn()

        if claimed_turn is None:
            return False
        request_data, request_message_id = claimed_turn
        await self.turn_processor.process(request_data, request_message_id)
        return True


    async def claimed_turn(self) -> tuple[dict[str, Any], str] | None:

        async with self.session_factory() as session:
            turn_service = TurnService(session)
            claimed_turn = await turn_service.claimed_turn(self.work_id)

            if claimed_turn is None:
                return None
            request_data, request_message_id = await  turn_service.build_turn(claimed_turn)
            await session.commit()
            return request_data, request_message_id

    async def _recover_expired_turns(self) ->None:
        async with self.session_factory() as session:
            turn_service = TurnService(session)
            turns_and_conversations = await turn_service.list_expired_running_turns_with_conversation()
            for turn,conversation in turns_and_conversations:
                if conversation.input_revision != turn.snapshot_revision:
                    turn_service.mark_superseded(turn)
                else:
                    turn_service.requeue(turn, RuntimeError("worker 租约超时"))
            if turns_and_conversations:
                await session.commit()

async def main_async():
    await AIWorker().start()

if __name__ == '__main__':
    run_async(main_async())
