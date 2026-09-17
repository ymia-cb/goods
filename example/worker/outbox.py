import asyncio
import json
import logging

from redis import RedisError

from example.app.respositories.outbox import OutboxRepository
from example.app.services.realtime import build_realtime_event
from example.common.config import get_settings
from example.common.event_loop import run_async
from example.infrastucture.db import session_factory, db_engine
from example.infrastucture.redis import redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


class OutboxWorker:
    def __init__(self):
        self.settings = get_settings()
        self.session_factory = session_factory
        self.redis = redis_client


    async def start(self):
        logger.info("realtimeoutbox worker 已经启动")

        while True:
            try:
                published = await  self.publish_next_event()
            except Exception:
                logger.exception("realtimeoutbix worker 事件处理失败")
                published = False

            if not published:
                await asyncio.sleep(self.settings.outbox_publish_interval_seconds)


    async def publish_next_event(self) ->bool:
        async with self.session_factory() as session:
            outbox_repo = OutboxRepository(session)
            event = await outbox_repo.find_next_unpublished()
            if event is None:
                return False


            event_json = json.dumps(
                build_realtime_event(
                    event_id=event.id,
                    event_type=event.event_type,
                    event_data=event.data,
                    conversation_id=event.conversation_id,
                    event_create_at=event.created_at,
                ),
                ensure_ascii=False
            )
            try:
                await self.redis.publish(event.channel, event_json)
            except RedisError:
                outbox_repo.mark_published_failed(event)
                await session.commit()
                logger.exception("realtimeoutbox worker 事件发布失败",event.id)
                return False
            outbox_repo.mark_published_succeeded(event)
            await session.commit()
            return True

async def main_async():
    try:
        await OutboxWorker().start()
    finally:
        await redis_client.aclose()
        await db_engine.dispose()


if __name__ == '__main__':
    run_async(main_async())