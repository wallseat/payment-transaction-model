from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from transaction.core import connection_store


async def get_session() -> AsyncGenerator:
    async with AsyncSession(
        connection_store.sqla_engine, expire_on_commit=False
    ) as session:
        yield session


async def get_channel() -> AsyncGenerator:
    async with connection_store.rbmq_channel_pool.acquire() as channel:
        yield channel
