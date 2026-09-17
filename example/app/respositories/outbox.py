from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from example.common.utils import get_utcnow
from example.models.models import RealtimeOutbox


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add(self, event: RealtimeOutbox) -> None:
        """将实时事件加入当前数据库事务。"""
        self.session.add(event)

    async def find_next_unpublished(self) -> RealtimeOutbox | None:
        return  await self.session.scalar(
            select(RealtimeOutbox)
            .where(RealtimeOutbox.published_at.is_(None))
            .order_by(RealtimeOutbox.sequence)
            .limit(1)
        )

    @staticmethod
    def mark_published_succeeded(event: RealtimeOutbox):
        event.attempts += 1
        event.published_at = get_utcnow()

    @staticmethod
    def mark_published_failed(event: RealtimeOutbox):
        event.attempts += 1
