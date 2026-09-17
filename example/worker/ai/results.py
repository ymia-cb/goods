from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from example.app.respositories.chat.message import MessageRepository
from example.app.services.admin.handoff import HandoffService
from example.app.services.realtime import RealTimeOutBoxService
from example.common.utils import get_uid, get_utcnow
from example.models.models import Conversation, ConversationTurn, Message, Handoff


class AIResultService:
    def __init__(self, session: AsyncSession):
        self.message_repo = MessageRepository(session)
        self.real_service = RealTimeOutBoxService(session)
        self.handoff_service = HandoffService(session)

    def save_ai_result(self, conversation: Conversation, turn: ConversationTurn, content: dict[str, Any], *, message_id: str | None = None) -> Message:
        message = Message(
            message_id=message_id or get_uid("msg"),
            conversation_id=conversation.id,
            role="ai",
            message_type="text",
            content=content,
            agent_run_id=turn.id,
            agent_outcome_seq=1
        )
        self.message_repo.add_message(message)
        conversation.last_active_at = get_utcnow()
        self.real_service.add_message_created_events(conversation, message, notify_user=True,notify_satff=False)
        return message

    async def save_hand_off_result(self, conversation: Conversation, turn: ConversationTurn, event_data: dict[str, Any]) -> Handoff:
        handoff = await self.handoff_service.get_or_create_open_handoff(conversation, summary=str(event_data["summary"]))

        conversation.mode = "QUEUED"
        self.save_ai_result(conversation, turn, event_data["content"], message_id=event_data.get("message_id"))

        self.real_service.add_handoff_changed_events(conversation, handoff)
        return handoff