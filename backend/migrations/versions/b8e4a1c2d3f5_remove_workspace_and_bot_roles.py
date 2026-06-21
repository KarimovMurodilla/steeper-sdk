"""remove workspace multi-tenant tables; bots owned by users

Revision ID: b8e4a1c2d3f5
Revises: 3c7a9b2e1f4d
Create Date: 2026-04-12 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8e4a1c2d3f5"
down_revision: str | None = "3c7a9b2e1f4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("owner_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_bots_owner_id_users",
        "bots",
        "users",
        ["owner_id"],
        ["id"],
    )

    op.execute(
        """
        UPDATE bots SET owner_id = (
            SELECT wm.user_id FROM workspace_members wm
            WHERE wm.workspace_id = bots.workspace_id
              AND wm.role = 'OWNER'
              AND wm.is_deleted IS FALSE
            LIMIT 1
        )
        """
    )
    op.execute(
        """
        UPDATE bots SET owner_id = (
            SELECT wm.user_id FROM workspace_members wm
            WHERE wm.workspace_id = bots.workspace_id
              AND wm.is_deleted IS FALSE
            LIMIT 1
        )
        WHERE owner_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE bots SET owner_id = (
            SELECT abr.admin_id FROM admin_bot_roles abr
            WHERE abr.bot_id = bots.id
            LIMIT 1
        )
        WHERE owner_id IS NULL
        """
    )

    op.alter_column("bots", "owner_id", nullable=False)

    op.drop_table("admin_bot_roles")
    op.drop_constraint("fk_bots_workspace_id_workspaces", "bots", type_="foreignkey")
    op.drop_column("bots", "workspace_id")

    op.drop_table("workspace_members")
    op.drop_table("workspaces")

    op.execute("DROP TYPE IF EXISTS workspacerole")
    op.execute("DROP TYPE IF EXISTS botrole")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")
