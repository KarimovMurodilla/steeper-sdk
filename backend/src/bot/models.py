from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SQLEnum,
    Index,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.bot.enums import BotStatus
from src.core.database.base import Base
from src.core.database.mixins import SoftDeleteMixin, TimestampMixin, UUIDIDMixin

if TYPE_CHECKING:
    from src.communication.models import Chat
    from src.crm.models import TelegramUser


class Bot(Base, UUIDIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "bots"

    __table_args__ = (
        Index(
            "uq_bots_username_not_deleted",
            "username",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )

    name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(255))
    token_encrypted: Mapped[str] = mapped_column(String(1000))
    status: Mapped[BotStatus] = mapped_column(
        SQLEnum(BotStatus), default=BotStatus.ACTIVE
    )

    # Relationships
    telegram_users: Mapped[list["TelegramUser"]] = relationship(
        "TelegramUser", back_populates="bot"
    )
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="bot")
