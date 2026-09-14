from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from example.models.models import Message, Conversation


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_conversation_messages(self, conversation_id: str) -> list[Message]:

        results = await self.session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
        )
        return list(results.all())

    async def get_conversation_message(self, user_id) -> tuple[Conversation, Message]:
         result =  await self.session.execute(
            select(Conversation)
            .join(Message)
            .where(Conversation.user_id == user_id)
        )
         return result

    def add_message(self, message):
        self.session.add(message)

