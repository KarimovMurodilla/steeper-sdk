from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.base import Base
from src.core.database.mixins import (
    SoftDeleteMixin,
    TimestampMixin,
    UUIDIDMixin,
)


class User(Base, UUIDIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "uq_users_username_not_deleted",
            "username",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "uq_users_login_not_deleted",
            "login",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )

    username: Mapped[str | None] = mapped_column(String(60), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Password-based authentication (optional; set by admin)
    login: Mapped[str | None] = mapped_column(String(60), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def full_name(self) -> str:
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        if parts:
            return " ".join(parts)
        if self.username:
            return self.username
        if self.login:
            return self.login
        return str(self.id) if self.id is not None else "User"
