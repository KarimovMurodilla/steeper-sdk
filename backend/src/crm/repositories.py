from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from loggers import get_logger
from src.core.database.repositories import SoftDeleteRepository
from src.crm.models import TelegramUser

logger = get_logger(__name__)


class TelegramUserRepository(SoftDeleteRepository[TelegramUser]):
    model = TelegramUser

    async def upsert(
        self, session: AsyncSession, bot_id: UUID, tg_data: dict[str, Any]
    ) -> TelegramUser:
        """
        Creates or updates a TelegramUser.
        Since we have a unique constraint (tg_user_id, bot_id), we use upsert.
        """
        stmt = (
            insert(self.model)
            .values(
                bot_id=bot_id,
                tg_user_id=tg_data["id"],
                first_name=tg_data.get("first_name"),
                username=tg_data.get("username"),
                language_code=tg_data.get("language_code"),
            )
            .on_conflict_do_update(
                index_elements=["tg_user_id", "bot_id"],
                set_={
                    "first_name": tg_data.get("first_name"),
                    "username": tg_data.get("username"),
                    "language_code": tg_data.get("language_code"),
                    "updated_at": func.now(),
                    "deleted_at": None,
                    "is_deleted": False,
                },
            )
            .returning(self.model)
        )

        result = await session.execute(stmt)
        return result.scalar_one()

    async def get_targeted_users(
        self, session: AsyncSession, bot_id: UUID, cutoff_date: Any | None = None
    ) -> list[TelegramUser]:
        """
        Retrieves all active Telegram users for a specific bot,
        optionally filtering by those updated after a cutoff date.
        """
        query = select(self.model).where(
            self.model.bot_id == bot_id,
            self.model.is_deleted.is_(False),
        )
        if cutoff_date is not None:
            query = query.where(self.model.updated_at >= cutoff_date)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_by_bot(self, session: AsyncSession, bot_id: UUID) -> int:
        """Total non-deleted TelegramUsers for a bot."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.bot_id == bot_id, self.model.is_deleted.is_(False))
        )
        return int((await session.execute(stmt)).scalar_one())

    def _bot_window(
        self,
        bot_id: UUID,
        since: datetime | None,
        until: datetime | None,
    ) -> list[Any]:
        """Bot scope plus an optional ``[since, until)`` window over creation."""
        conditions: list[Any] = [
            self.model.bot_id == bot_id,
            self.model.is_deleted.is_(False),
        ]
        if since is not None:
            conditions.append(self.model.created_at >= since)
        if until is not None:
            conditions.append(self.model.created_at < until)
        return conditions

    async def new_users_timeseries(
        self,
        session: AsyncSession,
        bot_id: UUID,
        granularity: str = "day",
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[datetime, int]]:
        """First-seen users bucketed by ``granularity`` (day/hour/week/month)."""
        bucket = func.date_trunc(granularity, self.model.created_at)
        stmt = (
            select(bucket.label("bucket"), func.count())
            .where(*self._bot_window(bot_id, since, until))
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = (await session.execute(stmt)).all()
        return [(bucket_value, int(count)) for bucket_value, count in rows]

    async def count_by_language(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[str, int]]:
        """User counts grouped by ``language_code``."""
        stmt = (
            select(self.model.language_code, func.count())
            .where(
                *self._bot_window(bot_id, since, until),
                self.model.language_code.is_not(None),
            )
            .group_by(self.model.language_code)
            .order_by(func.count().desc())
        )
        rows = (await session.execute(stmt)).all()
        return [(str(language_code), int(count)) for language_code, count in rows]

    async def get_display_names(
        self, session: AsyncSession, bot_id: UUID, tg_user_ids: list[int]
    ) -> dict[int, tuple[str | None, str | None]]:
        """Map ``tg_user_id`` to its ``(first_name, username)`` pair."""
        if not tg_user_ids:
            return {}

        stmt = select(
            self.model.tg_user_id, self.model.first_name, self.model.username
        ).where(
            self.model.bot_id == bot_id,
            self.model.tg_user_id.in_(tg_user_ids),
        )
        rows = (await session.execute(stmt)).all()
        return {
            int(tg_user_id): (first_name, username)
            for tg_user_id, first_name, username in rows
        }
