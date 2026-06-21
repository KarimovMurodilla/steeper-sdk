from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID as PY_UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.communication.enums import (
    ChatStatus,
    ContentType,
    MessageType,
    SenderType,
    UpdateType,
)
from src.core.database.base import Base
from src.core.database.mixins import (
    SoftDeleteMixin,
    TimestampMixin,
    UUID7IDMixin,
    UUIDIDMixin,
)

if TYPE_CHECKING:
    from src.bot.models import Bot
    from src.crm.models import TelegramUser


class Chat(Base, UUIDIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chats"

    bot_id: Mapped[PY_UUID] = mapped_column(ForeignKey("bots.id"), nullable=False)
    telegram_user_id: Mapped[PY_UUID] = mapped_column(
        ForeignKey("telegram_users.id"), nullable=False
    )
    status: Mapped[ChatStatus] = mapped_column(
        SQLEnum(ChatStatus), default=ChatStatus.OPEN
    )

    # Relationships
    bot: Mapped["Bot"] = relationship("Bot", back_populates="chats")
    telegram_user: Mapped["TelegramUser"] = relationship(
        "TelegramUser", back_populates="chats"
    )
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="chat")


class Message(Base, UUID7IDMixin, TimestampMixin):
    __tablename__ = "messages"

    chat_id: Mapped[PY_UUID] = mapped_column(ForeignKey("chats.id"), nullable=False)
    sender_type: Mapped[SenderType] = mapped_column(SQLEnum(SenderType))
    message_type: Mapped[MessageType] = mapped_column(SQLEnum(MessageType))

    tg_message_id: Mapped[int | None] = mapped_column(nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_info: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict
    )  # For media_id, caption and etc.

    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")


class TelegramUpdate(Base, UUID7IDMixin, TimestampMixin):
    """Append-only log of every raw Telegram Update received by a bot.

    The full payload is stored verbatim in ``raw`` so that no incoming data is
    ever lost — even update types we do not process yet. The flat dimension
    columns (``update_type``, ``content_type``, ``tg_user_id`` ...) are
    extracted on ingest purely to make analytics filtering/aggregation cheap;
    ``raw`` remains the source of truth. ``created_at`` (from ``TimestampMixin``)
    is the ingest time; ``tg_date`` is Telegram's own message timestamp.
    """

    __tablename__ = "telegram_updates"
    __table_args__ = (
        # Telegram retries deliveries on non-2xx; this makes ingest idempotent.
        UniqueConstraint("bot_id", "update_id", name="uq_tg_update_bot_update_id"),
        Index("idx_tg_update_bot_type", "bot_id", "update_type"),
        Index("idx_tg_update_bot_content", "bot_id", "content_type"),
        Index("idx_tg_update_bot_date", "bot_id", "tg_date"),
        Index("idx_tg_update_bot_user", "bot_id", "tg_user_id"),
    )

    bot_id: Mapped[PY_UUID] = mapped_column(ForeignKey("bots.id"), nullable=False)
    update_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    update_type: Mapped[UpdateType] = mapped_column(SQLEnum(UpdateType), nullable=False)

    # Extracted dimensions (nullable: not every update type carries them).
    tg_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tg_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    chat_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content_type: Mapped[ContentType | None] = mapped_column(
        SQLEnum(ContentType), nullable=True
    )
    tg_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Whether the update produced domain side-effects (Chat/Message, etc.).
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)

    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
