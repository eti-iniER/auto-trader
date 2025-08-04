import datetime
import uuid
from decimal import Decimal
from typing import List, Optional

from app.db.enums import LogType, UserSettingsMode
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, unique=True
    )
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings", back_populates="user", cascade="all, delete-orphan"
    )
    instruments: Mapped[List["Instrument"]] = relationship(
        "Instrument",
        back_populates="user",
        cascade="all, delete",
        order_by="desc(Instrument.updated_at)",
    )


class Instrument(BaseDBModel):
    __tablename__ = "instruments"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", back_populates="instruments")
    market_and_symbol: Mapped[str] = mapped_column(String(255), nullable=False)
    ig_epic: Mapped[str] = mapped_column(String(255), nullable=False)
    yahoo_symbol: Mapped[str] = mapped_column(String(255), nullable=False)
    atr_stop_loss_period: Mapped[int] = mapped_column(nullable=False)
    atr_stop_loss_multiple: Mapped[Decimal] = mapped_column(
        nullable=False, default=Decimal("1.0")
    )
    atr_profit_target_period: Mapped[int] = mapped_column(nullable=False)
    atr_profit_multiple: Mapped[Decimal] = mapped_column(
        nullable=False, default=Decimal("1.0")
    )
    position_size: Mapped[int] = mapped_column(nullable=False, default=1)
    max_position_size: Mapped[int] = mapped_column(nullable=True)
    opening_price_multiple: Mapped[Decimal] = mapped_column(
        nullable=False, default=Decimal("1.0")
    )
    next_dividend_date: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class UserSettings(BaseDBModel):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped[User] = relationship("User", back_populates="settings", uselist=False)
    mode: Mapped[UserSettingsMode] = mapped_column(
        Enum(UserSettingsMode), nullable=False, default=UserSettingsMode.DEMO
    )
    demo_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    demo_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    demo_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    demo_webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    live_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    live_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    live_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    live_webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
