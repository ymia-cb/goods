from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, func

from example.models.models import Conversation, Message, Handoff


class AdminMetricsRepository:

    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_metrics(
        self
    ) -> dict[str, int]:
        statement = select(
            select(func.count(Conversation.id)).label("conversations"),
            select(func.count(Message.id)).scalar_subquery().label("messages"),
            select(func.count(Handoff.id)).scalar_subquery().label("handoffs"),
            select(func.count(Conversation.id)).where(Conversation.mode == "QUEUED").scalar_subquery().label("queued"),
            select(func.count(Conversation.id)).where(Conversation.mode == "HUMAN").scalar_subquery().label("human")

        )
        row = (await self.session.execute(statement)).one()
        return {
            "conversations": row.conversations,
            "messages": row.messages,
            "handoffs": row.handoffs,
            "queued": row.queued,
            "human": row.human
        }