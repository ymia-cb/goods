from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from example.app.respositories.outbox import OutboxRepository
from example.app.schemas.event import RealTimeOutBoxType
from example.common.utils import get_uid
from example.models.models import Message, RealtimeOutbox, Conversation, Handoff

STAFF_CHANNEL = "customer-service:staff"

USER_CHANNEL_PREFIX = "customer-service:user:"


def user_channel(user_id: str) -> str:
    """返回指定用户的实时事件频道。"""
    return f"{USER_CHANNEL_PREFIX}{user_id}"


def build_message_created_data(message: Message) -> dict[str, Any]:
    """构建消息创建事件的数据。"""
    return {
        "message": {
            "message_id": message.message_id,
            "role": message.role,
            "content": message.content,
        }
    }


def build_handoff_changed_data(handoff: Handoff, conversation: Conversation) -> dict[str, Any]:
    """构建工单状态变化事件的数据。"""
    return {
        "handoff_id": handoff.id,
        "status": handoff.status,
        "summary": handoff.summary,
        "assigned_agent_id": handoff.assigned_agent_id,
        "conversation_mode": conversation.mode
    }

def build_realtime_event(event_id: str, event_type: str, event_data: dict[str, Any], conversation_id: str, event_create_at: datetime) -> dict[str, Any]:
    """构建实时事件数据。"""
    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_data": event_data,
        "event_create_at": event_create_at.isoformat(),
        "conversation_id": conversation_id,

    }

def build_message_event_data(message: Message) -> dict[str, Any]:
    return {
        "message": {
            "message_id": message.message_id,
            "role": message.role,
            "content": message.content,
        }
    }




class RealTimeOutBoxService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.outbox_repo = OutboxRepository(session)


    def add_realtime_outbox(self,event_channel: str,
                            event_data: dict[str, Any],
                            event_type: RealTimeOutBoxType,
                            conversation_id: str,
                            message_id: str | None,
):
        outbox = RealtimeOutbox(
            channel=event_channel,
            data=event_data,
            event_type=event_type,
            conversation_id=conversation_id,
            request_message_id=message_id or get_uid("conversation_id"),
        )

        self.session.add(outbox)


    def add_message_created_events(self, conversation: Conversation,message: Message,*,notify_user: bool,notify_staff: bool):
        channels: list[str] = []
        if notify_user:
            channels.append(user_channel(conversation.user_id))
        if notify_staff:
            channels.append(STAFF_CHANNEL)
        for channel in channels:
            self.add_outbox_event(channel, RealTimeOutBoxType.MESSAGE_CREATED, build_message_event_data(message),conversation_id=conversation.id)

    def add_handoff_changed_events(self, conversation: Conversation,handoff: Handoff):

        for channel in (user_channel(conversation.user_id), STAFF_CHANNEL):
            self.add_outbox_event(channel, RealTimeOutBoxType.HANDOFF_CHANGED, build_handoff_changed_data(handoff, conversation), conversation_id=conversation.id)

    def add_outbox_event(self, channel: str, event_type: RealTimeOutBoxType,event_data: dict[str, Any], *,conversation_id: str) -> RealtimeOutbox:
        event = RealtimeOutbox(
            channel=channel,
            data=event_data,
            event_type=event_type,
            conversation_id=conversation_id,

        )
        self.outbox_repo.add(event)
        return event
