from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from example.models.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_active_conversation(self, conversation_id: str, model: tuple[str, ...]) ->Conversation | None:

        return  await self.session.scalar(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.mode.in_(model))
            .order_by(Conversation.last_active_at.desc())
            .limit(1)

        )

    async def add(self, user_id: str) -> Conversation:

        conversation = Conversation(user_id=user_id,mode="AI")

        self.session.add(conversation)
        await self.session.flush()

        return conversation


    async def get_ai_conversation(self, user_id : str) -> Conversation | None:

        return await self.session.scalar(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.mode == "AI")
        )


    async def get_conversation(self, conversation_id: str) -> Conversation | None:

        return await self.session.get(Conversation, conversation_id)