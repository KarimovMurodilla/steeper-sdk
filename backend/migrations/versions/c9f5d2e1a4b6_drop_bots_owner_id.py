"""drop bots.owner_id

Revision ID: c9f5d2e1a4b6
Revises: b8e4a1c2d3f5
Create Date: 2026-04-12 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9f5d2e1a4b6"
down_revision: str | None = "b8e4a1c2d3f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("fk_bots_owner_id_users", "bots", type_="foreignkey")
    op.drop_column("bots", "owner_id")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")
