"""add login and password_hash to users

Revision ID: 3c7a9b2e1f4d
Revises: f1d8f11de7e7
Create Date: 2026-04-12 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3c7a9b2e1f4d"
down_revision: str | None = "f1d8f11de7e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("login", sa.String(60), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(256), nullable=True))
    op.create_index(
        "uq_users_login_not_deleted",
        "users",
        ["login"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_login_not_deleted", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "login")
