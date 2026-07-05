"""bots username partial unique (exclude soft-deleted)

Revision ID: b7d3e9f1a2c4
Revises: a4c5d6e7f8a9
Create Date: 2026-06-28 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7d3e9f1a2c4"
down_revision: str | None = "a4c5d6e7f8a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_bots_username", "bots", type_="unique")
    op.create_index(
        "uq_bots_username_not_deleted",
        "bots",
        ["username"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_bots_username_not_deleted", table_name="bots")
    op.create_unique_constraint("uq_bots_username", "bots", ["username"])
