import json
import uuid
from decimal import Decimal

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.channel import Channel
from aio_pika.pool import Pool
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from transaction.api.providers import get_channel, get_session
from transaction.api.schemas import TransactionInfo
from transaction.core import connection_store, settings
from transaction.models import TransactionStatus, User, UserTransaction

api_router = APIRouter(prefix="/api")


@api_router.get("/pay", response_model=TransactionInfo)
async def pay(
    amount: Decimal,
    source: int,
    dest: int,
    *,
    session: AsyncSession = Depends(get_session),
    channel: Channel = Depends(get_channel),
):
    if not (src_user := await session.get(User, source)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source user not found",
        )

    if not (dest_user := await session.get(User, dest)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination user not found",
        )

    if src_user.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough money",
        )

    async with session.begin_nested():
        src_user.balance -= amount

        transaction_id = uuid.uuid4()

        transaction = UserTransaction(
            id=transaction_id,
            user_src_id=src_user.id,
            user_dest_id=dest_user.id,
            amount=amount,
        )

        transaction_status = TransactionStatus(
            transaction_id=transaction_id,
            status="pending",
        )

        session.add(transaction)
        session.add(transaction_status)
        session.add(src_user)

        await session.commit()

    await channel.declare_queue(settings.TRANSACTIONS_QUEUE, durable=True)
    await channel.default_exchange.publish(
        aio_pika.Message(
            json.dumps(  # XXX: It's better to define a dataclass or a typed dict
                {
                    "transaction_id": str(transaction_id),
                    "src_id": src_user.id,
                    "dest_id": dest_user.id,
                    "amount": float(
                        amount
                    ),  # XXX: Or we can use external orjson library, that can serialize Decimal
                }
            ).encode("utf-8")
        ),
        settings.TRANSACTIONS_QUEUE,
    )

    return TransactionInfo(
        destination=dest_user.name,
        status=transaction_status.status,
        amount=amount,
    )


app = FastAPI(title="Transaction API")
app.include_router(api_router)


@app.on_event("startup")
async def startup():
    async def get_connection() -> AbstractRobustConnection:
        return await aio_pika.connect_robust(settings.RABBITMQ_DSN)

    connection_pool: Pool = Pool(get_connection, max_size=1)

    async def get_channel() -> Channel:
        async with connection_pool.acquire() as connection:
            return await connection.channel()

    channel_pool: Pool = Pool(get_channel, max_size=10)

    connection_store.rbmq_channel_pool = channel_pool
    connection_store.sqla_engine = create_async_engine(settings.POSTGRES_DSN)
