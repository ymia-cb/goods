from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from example.common.config import get_settings
from example.common.utils import get_utcnow
from example.models.models import Conversation, Message
from example.app.respositories.conversation import ConversationRepository
from example.app.respositories.message import MessageRepository
from example.app.respositories.turn import ConversationTurnRepository



class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.turn_repo = ConversationTurnRepository(session)
        self.message_repo = MessageRepository(session)

    async def get_current_conversation(self, user_id: str) -> dict[str, Any]:

        conversation = await self.ensure_activate_conversation(user_id)

        is_processing = await self.turn_repo.is_activate_turn(conversation.id)
        await self.session.commit()

        return {
            "id": conversation.id,
            "mode": conversation.mode,
            "is_processing": is_processing,
        }


    async def ensure_activate_conversation(self, user_id: str) -> Conversation:
        await self._close_timeout_conversation(user_id)

        conversation = await self.conversation_repo.find_active_conversation(user_id, "AI", "QUEUED", "HUMAN")
        if conversation:
            return conversation

        return await self._create_ai_conversation(user_id)

    async def _create_ai_conversation(self, user_id: str) -> Conversation:
        return  await self.conversation_repo.add(user_id)

    async def _close_timeout_conversation(self, user_id: str):

        conversation = await self.conversation_repo.get_ai_conversation(user_id)
        if conversation is not None:
            flag = False
            if _has_idle_timeout(conversation):
                conversation.mode = "CLOSED"
                conversation.ended_at = conversation.last_active_at
                flag = True
            if flag:
                await self.session.flush()

    async def get_conversation_detail(self, conversation_id: str) -> dict[str, list[dict[str, Any]]]:

        conversation = await self.conversation_repo.get_conversation(conversation_id)
        if conversation is None:
            raise ValueError("当前用户会话不存在")

        conversation_messages = await self.message_repo.get_conversation_messages(conversation_id)

        return {
            "messages": [get_message_payload(message) for message in conversation_messages]
        }


def get_message_payload(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
    }

def _has_idle_timeout(conversation: Conversation) -> bool:
    now = get_utcnow()
    activate_at = conversation.last_active_at
    timeout = timedelta(minutes=get_settings().conversation_idle_timeout_minutes)

    return (now - activate_at) >= timeout


