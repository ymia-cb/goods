from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from example.models.models import Handoff, Conversation


class HandoffRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    def add(self, handoff: Handoff):
        self.session.add(handoff)


    async def find_open_by_user_id(self, user_id: str) ->Handoff | None:
        return await self.session.scalar(
            select(Handoff).where(Handoff.user_id == user_id, Handoff.status.in_(["waiting", "active"]))


        )

    async def list_open(self) -> list[Handoff]:
        records = await self.session.scalars(
            select(Handoff).where(Handoff.status.in_(["waiting", "active"])).order_by(Handoff.created_at.asc())
        )
        return list(records.all())

    async def find_and_lock_with_conversation_by_id(self, handoff_id: str) -> tuple[Handoff, Conversation]:
        result = await  self.session.execute(
            select(Handoff, Conversation)
            .join(Conversation, Conversation.id == Handoff.conversation_id)
            .where(Handoff.id == handoff_id)
            .with_for_update()
        )
        return result.tuples().one()