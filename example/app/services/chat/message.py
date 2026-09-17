from sqlalchemy.ext.asyncio import AsyncSession

from example.app.schemas.event import  RealTimeOutBoxType
from example.app.schemas.chat.message import ChatMessageRequest, MessageRole
from example.app.respositories.chat.message import MessageRepository
from example.app.services.chat.conversation import ConversationService
from example.app.services.chat.turn import TurnService
from example.app.services.realtime import RealTimeOutBoxService, STAFF_CHANNEL
from example.common.utils import get_utcnow
from example.models.models import Message, Conversation


class MessageService:

    def __init__(self, session: AsyncSession, conversation_service: ConversationService, turn_service: TurnService, outbox_service: RealTimeOutBoxService):
        self.session = session
        self.message_repo = MessageRepository(session)
        self.conversation_service = conversation_service
        self.turn_service = turn_service
        self.outbox_Service = outbox_service

    async def accept_message_user(self, chat_message: ChatMessageRequest, user_id: str):

        # user_id获取conversation和message表数据
        duplicate_result = await self.message_repo.get_conversation_message(chat_message.message_id)

        # message_id是否存在，存在直接返回
        if duplicate_result:
            message, conversation = duplicate_result
            return {
                "conversation_id": message.conversation_id,
                "mode": conversation.mode,
            }

        #不存在，   获取或者创建有效会话
        conversation = await self.conversation_service.ensure_locked_activate_conversation(user_id)

        message =  self.save_message(conversation, chat_message)

        if conversation.mode == "AI":
            await self.turn_service.add_message_to_turn(message, conversation)
        elif conversation.mode in ("QUEUED","HUMAN"):
            self.outbox_Service.add_realtime_outbox(
                STAFF_CHANNEL,
                RealTimeOutBoxType.MESSAGE_CREATED,
                conversation.id,
                chat_message.message_id,
            )
        else:
            raise ValueError(f"Unknown conversation mode: {conversation.mode}")

        await self.session.commit()
        return {
            "conversation_id": conversation.id,
            "mode": conversation.mode,
        }



    def save_message(self, conversation:Conversation, chat_message: ChatMessageRequest):
        message = Message(
            conversation_id=conversation.id,
            message_id=chat_message.message_id,
            message_type=chat_message.message_type,
            content=chat_message.content,
            role=MessageRole.USER,
        )
        message = self.message_repo.add_message(message)
        conversation.last_active_at = get_utcnow()
        return message








