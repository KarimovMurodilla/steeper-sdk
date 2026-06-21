"""drop audit_logs table

Revision ID: f3b4c5d6e7f8
Revises: e2a3b4c5d6f7
Create Date: 2026-04-12 18:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3b4c5d6e7f8"
down_revision: str | None = "e2a3b4c5d6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("audit_logs")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")
