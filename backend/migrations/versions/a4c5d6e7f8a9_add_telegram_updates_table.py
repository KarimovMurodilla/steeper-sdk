"""add telegram_updates table

Revision ID: a4c5d6e7f8a9
Revises: f3b4c5d6e7f8
Create Date: 2026-05-29 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a4c5d6e7f8a9"
down_revision: str | None = "f3b4c5d6e7f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPDATE_TYPE_LABELS = (
    "MESSAGE",
    "EDITED_MESSAGE",
    "CHANNEL_POST",
    "EDITED_CHANNEL_POST",
    "CALLBACK_QUERY",
    "INLINE_QUERY",
    "CHOSEN_INLINE_RESULT",
    "MY_CHAT_MEMBER",
    "CHAT_MEMBER",
    "CHAT_JOIN_REQUEST",
    "MESSAGE_REACTION",
    "MESSAGE_REACTION_COUNT",
    "POLL",
    "POLL_ANSWER",
    "PRE_CHECKOUT_QUERY",
    "SHIPPING_QUERY",
    "UNKNOWN",
)

CONTENT_TYPE_LABELS = (
    "TEXT",
    "PHOTO",
    "VIDEO",
    "VIDEO_NOTE",
    "ANIMATION",
    "AUDIO",
    "VOICE",
    "DOCUMENT",
    "STICKER",
    "LOCATION",
    "VENUE",
    "CONTACT",
    "POLL",
    "DICE",
    "SERVICE",
    "UNKNOWN",
)


def upgrade() -> None:
    sa.Enum(*UPDATE_TYPE_LABELS, name="updatetype").create(op.get_bind())
    sa.Enum(*CONTENT_TYPE_LABELS, name="contenttype").create(op.get_bind())

    op.create_table(
        "telegram_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "update_type",
            postgresql.ENUM(*UPDATE_TYPE_LABELS, name="updatetype", create_type=False),
            nullable=False,
        ),
        sa.Column("tg_user_id", sa.BigInteger(), nullable=True),
        sa.Column("tg_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("chat_type", sa.String(length=20), nullable=True),
        sa.Column(
            "content_type",
            postgresql.ENUM(
                *CONTENT_TYPE_LABELS, name="contenttype", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("tg_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["bot_id"],
            ["bots.id"],
            name=op.f("fk_telegram_updates_bot_id_bots"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_telegram_updates")),
        sa.UniqueConstraint(
            "bot_id", "update_id", name="uq_tg_update_bot_update_id"
        ),
    )
    op.create_index(
        "idx_tg_update_bot_type", "telegram_updates", ["bot_id", "update_type"]
    )
    op.create_index(
        "idx_tg_update_bot_content", "telegram_updates", ["bot_id", "content_type"]
    )
    op.create_index(
        "idx_tg_update_bot_date", "telegram_updates", ["bot_id", "tg_date"]
    )
    op.create_index(
        "idx_tg_update_bot_user", "telegram_updates", ["bot_id", "tg_user_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_tg_update_bot_user", table_name="telegram_updates")
    op.drop_index("idx_tg_update_bot_date", table_name="telegram_updates")
    op.drop_index("idx_tg_update_bot_content", table_name="telegram_updates")
    op.drop_index("idx_tg_update_bot_type", table_name="telegram_updates")
    op.drop_table("telegram_updates")
    sa.Enum(name="contenttype").drop(op.get_bind())
    sa.Enum(name="updatetype").drop(op.get_bind())
