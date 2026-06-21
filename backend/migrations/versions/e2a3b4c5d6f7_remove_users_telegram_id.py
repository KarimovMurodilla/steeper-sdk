"""remove users.telegram_id

Revision ID: e2a3b4c5d6f7
Revises: c9f5d2e1a4b6
Create Date: 2026-04-12 16:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e2a3b4c5d6f7"
down_revision: str | None = "c9f5d2e1a4b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(
        "uq_users_telegram_id_active_not_deleted",
        table_name="users",
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.drop_column("users", "telegram_id")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")
