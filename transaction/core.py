from dataclasses import dataclass
from typing import Any, Dict, Optional

from aio_pika.channel import Channel
from aio_pika.pool import Pool
from pydantic import BaseSettings, PostgresDsn, validator
from sqlalchemy.ext.asyncio import AsyncEngine


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    POSTGRES_DSN: Optional[PostgresDsn] = None

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASS: str

    RABBITMQ_DSN: Optional[str] = None

    TRANSACTIONS_QUEUE: str

    @validator("POSTGRES_DSN", pre=False)
    def assemble_postgres_dsn(
        cls,
        v: Optional[str],
        values: Dict[str, Any],
    ) -> str:
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            path=f"/{values.get('POSTGRES_DB')}",
        )

    @validator("RABBITMQ_DSN", pre=False)
    def assemble_rabbitmq_dsn(
        cls,
        v: Optional[str],
        values: Dict[str, Any],
    ) -> str:
        if isinstance(v, str):
            return v

        return f"amqp://{values.get('RABBITMQ_USER')}:{values.get('RABBITMQ_PASS')}@{values.get('RABBITMQ_HOST')}:{values.get('RABBITMQ_PORT')}/"

    class Config:
        env_file = ".env"


settings = Settings()


@dataclass
class ConnectionStore:
    sqla_engine: AsyncEngine = None
    rbmq_channel_pool: Pool[Channel] = None


connection_store = ConnectionStore()
