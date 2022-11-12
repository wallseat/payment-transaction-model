import uuid
from datetime import datetime
from typing import Any, Callable, List, Optional, Tuple, Type, TypeVar, Union

from sqlalchemy import (
    CheckConstraint,
    Column,
    Index,
    Integer,
    MetaData,
    Numeric,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import as_declarative, declared_attr

convention = {
    "ix": "ix__%(column_0_N_name)s",
    "uq": "uq__%(table_name)s__%(column_0_N_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(referred_table_name)s__%(column_0_name)s",
    "pk": "pk__%(table_name)s__%(column_0_N_name)s",
}

metadata = MetaData(naming_convention=convention)
SCHEMA = "transactions"


_T_Model = TypeVar("_T_Model")

_T_ColumnCollectionConstraint = Union[
    Index, PrimaryKeyConstraint, UniqueConstraint, CheckConstraint
]
_T_TableExtra = Union[
    _T_ColumnCollectionConstraint,
    Callable[[Type[_T_Model]], _T_ColumnCollectionConstraint],
]


@as_declarative(metadata=metadata)
class Base:
    __extra__: Tuple[Any, ...]
    __schema__: str = SCHEMA

    def __init_subclass__(
        cls, *args, extra: Optional[List[_T_TableExtra]] = None, **kwargs
    ) -> None:
        if extra is None:
            extra = []

        cls.__extra__ = tuple(obj(cls) if callable(obj) else obj for obj in extra)

    @declared_attr
    def __table_args__(cls):
        return (
            *cls.__extra__,
            {"schema": cls.__schema__},
        )


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    balance = Column(
        Numeric(18, 2),
        default=0,
        server_default=text("0"),
    )


class UserTransaction(
    Base,
    extra=[Index("ix__user_src_id", "user_src_id")],
):
    __tablename__ = "user_transaction"

    id = Column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
        primary_key=True,
    )
    user_src_id = Column(Integer, nullable=False)
    user_dest_id = Column(Integer, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    timestamp = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )


class TransactionStatus(
    Base,
    extra=[Index("ix__transaction_id", "transaction_id")],
):
    __tablename__ = "transaction_status"

    id = Column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
        primary_key=True,
    )
    transaction_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )
    status = Column(
        String(20), nullable=False
    )  # XXX: ENUM maybe, index scan optimization

    timestamp = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
    )
