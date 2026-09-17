from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from example.app.respositories.admin.handoff import HandoffRepository
from example.app.respositories.chat.message import MessageRepository
from example.app.services.realtime import RealTimeOutBoxService
from example.common.utils import get_utcnow, get_uid
from example.models.models import Conversation, Handoff, Message


class HandoffService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.handoff_repo = HandoffRepository(session)
        self.message_repo = MessageRepository(session)
        self.real_service = RealTimeOutBoxService(session)

    async def get_or_create_open_handoff(self, conversation: Conversation ,*, summary: str) -> Handoff:

        handoff = await self.handoff_repo.find_open_by_user_id(conversation.user_id)
        if handoff is not None:
            handoff.summary = summary
            return handoff

        handoff = Handoff(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            summary=summary,
            status="waiting",
        )
        self.handoff_repo.add(handoff)
        await self.session.flush()
        return handoff


    async def list_open_handoffs(self) -> list[Handoff]:
        return await self.handoff_repo.list_open()

    async def accept_handoff(self, handoff_id: str, agent_id: str):
        handoff, conversation = await self._get_open_handoff(handoff_id)
        if handoff.status == "active":
            self._require_owner(handoff, agent_id)
            return
        handoff.status = "active"
        handoff.agent_id = agent_id
        handoff.accepted_at = get_utcnow()
        conversation.mode = "HUMAN"
        conversation.last_active_at = get_utcnow()


        self.real_service.add_handoff_changed_events(conversation, handoff)
        await self.session.commit()

    async def replay_handoff(self, handoff_id: str, agent_id: str, *, message_id: str, text: str) -> None:
        handoff, conversation = await self._get_open_handoff(handoff_id)
        self._require_owner(handoff, agent_id)

        message = self._add_human_message(conversation, text, message_id=message_id)

        await self.session.flush()
        self.real_service.add_message_created_events(conversation, message, notify_user=True, notify_staff=True)
        await self.session.commit()


    async def resolve_handoff(self, handoff_id: str ,agent_id: str) -> None:
        handoff, conversation = await self._get_open_handoff(handoff_id)
        self._require_owner(handoff, agent_id)

        handoff.status = "resolved"
        handoff.resolved_at = get_utcnow()
        conversation.mode = "AI"
        conversation.last_active_at = get_utcnow()

        message = self._add_human_message(conversation,"人工客服已经结束服务，后续由AI继续服务")
        await self.session.flush()
        self.real_service.add_message_created_events(conversation, message, notify_user=True, notify_staff=False)

        self.real_service.add_handoff_changed_events(conversation, handoff)
        await self.session.commit()

    async def _get_open_handoff(self, handoff_id: str) -> tuple[Handoff, Conversation]:
        handoff_and_conversation = await self.handoff_repo.find_and_lock_with_conversation_by_id(handoff_id)
        handoff, conversation = handoff_and_conversation
        if handoff.status == 'resolved':
            raise  HTTPException(status_code=409, detail="工单已经结束")
        return handoff, conversation

    @staticmethod
    def _require_owner(handoff: Handoff, agent_id: str):
        if handoff.assigned_agent_id != agent_id:
            raise HTTPException(status_code=403, detail="订单不属于当前客服")


    def _add_human_message(self, conversation: Conversation, text: str, *, message_id: str) -> Message:

        message = Message(
            message_id=message_id or get_uid("msg"),
            conversation_id=conversation.id,
            role="human",
            message_type="text",
            content={"text": text},

        )
        self.message_repo.add_message(message)
        conversation.last_active_at = get_utcnow()
        return message