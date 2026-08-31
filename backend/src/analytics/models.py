"""Analytics domain models: raw product events and funnel definitions.

Unlike the rest of the analytics module — which aggregates tables owned by
``communication`` and ``crm`` — these two tables are owned here, because they
exist only to answer analytics questions.
"""

from datetime import datetime
from typing import Any
from uuid import UUID as PY_UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base
from src.core.database.mixins import (
    SoftDeleteMixin,
    TimestampMixin,
    UUID7IDMixin,
    UUIDIDMixin,
)


class BotEvent(Base, UUID7IDMixin, TimestampMixin):
    """Append-only log of product events reported by a bot process.

    A bot ships these through the ingestion endpoint to mark steps that are
    invisible in Telegram traffic — "pressed the pricing button", "finished
    onboarding", "paid". Only ``name`` and ``ts`` are stored as dimensions;
    everything else the bot wants to attach lives free-form in ``props``,
    which is deliberately not indexed.

    ``ts`` is the bot-side event time and the only ordering that matters for a
    funnel; ``created_at`` (from ``TimestampMixin``) is the ingest time and can
    lag it by the client's batching interval.

    The matching key for funnels is ``tg_user_id``, the raw Telegram id, never
    ``telegram_user_id``: the latter is resolved best-effort at ingest and is
    NULL when the event arrives before the user has ever messaged the bot.
    NULL would silently drop that user out of every step-to-step join.
    """

    __tablename__ = "bot_events"
    __table_args__ = (
        # Funnel entry: (bot, name) equality + a range on ts.
        Index("ix_bot_events_bot_name_ts", "bot_id", "name", "ts"),
        # Funnel step probes: three equality prefixes, a range on ts, and id
        # as the trailing tiebreak column so the LIMIT 1 lookup is index-only.
        Index("ix_bot_events_funnel", "bot_id", "tg_user_id", "name", "ts", "id"),
        # Joining events back to CRM records.
        Index("ix_bot_events_bot_user_ts", "bot_id", "telegram_user_id", "ts"),
    )

    bot_id: Mapped[PY_UUID] = mapped_column(ForeignKey("bots.id"), nullable=False)
    telegram_user_id: Mapped[PY_UUID | None] = mapped_column(
        ForeignKey("telegram_users.id"), nullable=True
    )
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    props: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Funnel(Base, UUIDIDMixin, TimestampMixin, SoftDeleteMixin):
    """A named, ordered sequence of event names with a conversion window.

    ``steps`` is a JSONB list of ``BotEvent.name`` values, in order. Repeating
    a name is legal and meaningful ("viewed a second item"). ``window_seconds``
    is measured from the *first* step, so it bounds the whole journey rather
    than each hop; see ``build_funnel_report_stmt``.
    """

    __tablename__ = "funnels"
    __table_args__ = (Index("ix_funnels_bot_id", "bot_id"),)

    bot_id: Mapped[PY_UUID] = mapped_column(ForeignKey("bots.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
