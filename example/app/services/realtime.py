from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from example.app.schemas.event import RealTimeOutBoxType
from example.common.utils import get_uid
from example.models.models import Message, RealtimeOutbox


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