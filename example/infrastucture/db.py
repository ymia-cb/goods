from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncEngine,
                                    create_async_engine,
                                    async_sessionmaker,
                                    AsyncSession)
from example.common.config import get_settings

db_engine :AsyncEngine = create_async_engine(get_settings().database_url,echo=False)


session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=db_engine,
    expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession]:


    async with session_factory as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e

