from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from example.app.respositories.chat.conversation import ConversationRepository
from example.app.respositories.chat.message import MessageRepository
from example.app.respositories.chat.turn import ConversationTurnRepository


from example.common.config import get_settings
from example.common.utils import get_utcnow
from example.models.models import Message, Conversation, ConversationTurn


class TurnService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.turn_repo = ConversationTurnRepository(session)
        self.message_repo = MessageRepository(session)
        self.conv_repo = ConversationRepository(session)


    async def add_message_to_turn(self, message: Message, conversation: Conversation) ->ConversationTurn:

        conversation.input_revision += 1
        message.input_revision = conversation.input_revision
        turn = await self.turn_repo.find_conversation_by_id(conversation.id)

        now = get_utcnow()

        delay = timedelta(milliseconds=self.settings.message_merge_delay_ms)

        if turn:
            turn.collect_until = min(now + delay, turn.max_collect_until)
            return turn
        turn = ConversationTurn(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            status="COLLECTING",
            collect_until=now + delay,
            start_revision=conversation.answered_revision+1,
            max_collect_until=now + timedelta(milliseconds=self.settings.message_merge_max_wait_ms)
        )
        self.turn_repo.add_turn(turn)
        return turn

    async def claimed_turn(self, worker_id: str) -> ConversationTurn | None:
        now = get_utcnow()

        turn_and_conversation = await self.turn_repo.find_ready_turn_conversation_by_lock(now)
        if turn_and_conversation is None:
            return None

        turn, conversation = turn_and_conversation
        turn.status = "RUNNING"
        turn.snapshot_revision = conversation.input_revision
        turn.locked_by = worker_id
        turn.locked_until = now + timedelta(seconds=self.settings.ai_worker_lease_seconds)
        turn.start_at = turn.start_at or now
        return turn

    async def build_turn(self, turn: ConversationTurn) ->  tuple[dict[str, Any], str]:

        snapshot_revision = turn.snapshot_revision
        current_messages = await self.message_repo.find_current_message_by_turn_range(turn.conversation_id, turn.start_revision, snapshot_revision)
        history_messages = list(reversed(await self.message_repo.find_history_messages_by_sequence(turn.conversation_id, current_messages[0].id)))
        return {
            "conversation_id": turn.conversation_id,
            "user_id": turn.user_id,
            "turn_id": turn.id,
            "request_id": f"{turn.id}:attempt:{turn.attempts}",
            "input_revision": snapshot_revision,
            "messages": [
                {
                    "message_id": message.message_id,
                    "type": message.message_type,
                    "content": message.content,
                }
                for message in current_messages
            ],
            "history": [
                {
                    "message_id": message.message_id,
                    "role": message.role,
                    "type": message.message_type,
                    "content": message.content,
                    "created_at": message.created_at.isoformat()
                }
                for message in history_messages
            ],
        }, current_messages[-1].message_id

    async  def find_turn_conversation_by_id(self,turn_id:str)->tuple[ConversationTurn,Conversation]:
       return await self.turn_repo.find_turn_conversation_by_id(turn_id)

    def mark_superseded(self, turn: ConversationTurn):
        turn.status = "SUPERSEDED"
        turn.finished_at = get_utcnow()
        TurnService._release_lease(turn)

    async def list_expired_running_turns_with_conversation(self) -> list[tuple[ConversationTurn, Conversation]]:
        turns = await self.turn_repo.list_expired_running_turns(get_utcnow())
        result: list[tuple[ConversationTurn, Conversation]] = []
        for turn in turns:
            conv = await self.conv_repo.get_and_lock_by_id(turn.conversation_id)
            result.append((turn, conv))
        return result



    def retry_or_fail(self,
                      turn: ConversationTurn,
                      error: Exception):
        turn.last_error = str(error)
        self._release_lease(turn)
        if turn.attempts < self.settings.ai_worker_max_attempts:
            turn.status = "COLLECTING"
            turn.collect_until = get_utcnow() + timedelta(
                seconds=self.settings.ai_worker_retry_delay_seconds
            )
            turn.run_id = None
            return True

        turn.status = "FAILED"
        turn.finished_at = get_utcnow()
        return False

    @staticmethod
    def _release_lease(turn: ConversationTurn):
        turn.locked_by = None
        turn.locked_until = None

    def requeue(self, turn: ConversationTurn, error: Exception) -> None:
        turn.status = "COLLECTING"
        turn.collect_until = get_utcnow()
        turn.run_id = None
        turn.last_error = str(error)
        self._release_lease(turn)