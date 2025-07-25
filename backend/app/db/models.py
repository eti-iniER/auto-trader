import datetime
import uuid

from sqlalchemy import DateTime, JSON, Text, Enum
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
from app.db.enums import LogType


class Base(AsyncAttrs, DeclarativeBase):
    pass


class BaseDBModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class Log(BaseDBModel):
    __tablename__ = "logs"

    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[LogType] = mapped_column(
        Enum(LogType), nullable=False, default=LogType.UNSPECIFIED
    )
    extra: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)


class User(BaseDBModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
