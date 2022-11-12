import asyncio
import json
import logging
import random
from decimal import Decimal

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.channel import Channel
from aio_pika.pool import Pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from transaction.core import connection_store, settings
from transaction.models import TransactionStatus, User


async def get_connection() -> AbstractRobustConnection:
    return await aio_pika.connect_robust(settings.RABBITMQ_DSN)


connection_pool: Pool = Pool(get_connection, max_size=1)


async def get_channel() -> Channel:
    async with connection_pool.acquire() as connection:
        return await connection.channel()


channel_pool: Pool = Pool(get_channel, max_size=10)


def startup() -> None:
    connection_store.rbmq_channel_pool = channel_pool
    connection_store.sqla_engine = create_async_engine(settings.POSTGRES_DSN)


async def main() -> None:
    startup()
    logging.basicConfig(level=logging.DEBUG)

    async with channel_pool.acquire() as channel:  # type: aio_pika.Channel
        channel: Channel

        await channel.set_qos(10)

        queue = await channel.declare_queue(
            settings.TRANSACTIONS_QUEUE,
            durable=True,
        )

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:

                async with AsyncSession(
                    connection_store.sqla_engine, expire_on_commit=False
                ) as session:
                    data = json.loads(message.body.decode("utf-8"))

                    transaction_status = TransactionStatus(
                        transaction_id=data["transaction_id"],
                        status="processing",
                    )

                    session.add(transaction_status)
                    await session.commit()

                    await asyncio.sleep(random.randint(3, 10))  # Business logic

                    if random.randint(0, 9) > 4:
                        user = await session.get(User, data["dest_id"])
                        user.balance += Decimal(data["amount"])

                        transaction_status = TransactionStatus(
                            transaction_id=data["transaction_id"],
                            status="approved",
                        )
                    else:
                        user = await session.get(User, data["src_id"])
                        user.balance += Decimal(data["amount"])

                        transaction_status = TransactionStatus(
                            transaction_id=data["transaction_id"],
                            status="rejected",
                        )

                    session.add(user)
                    session.add(transaction_status)
                    await session.commit()

                    await message.ack()


if __name__ == "__main__":
    asyncio.run(main())
