from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from loggers import get_logger
from src.communication.models import TelegramUpdate
from src.core.database.repositories import BaseRepository

logger = get_logger(__name__)


class TelegramUpdateRepository(BaseRepository[TelegramUpdate]):
    model = TelegramUpdate

    async def record(self, session: AsyncSession, values: dict[str, Any]) -> bool:
        """Idempotently persist one raw Telegram update.

        Uses ``INSERT ... ON CONFLICT DO NOTHING`` on the
        ``(bot_id, update_id)`` unique constraint so that Telegram's webhook
        retries do not create duplicate rows.

        Returns:
            bool: True if a new row was inserted, False if it was a duplicate.
        """
        stmt = (
            pg_insert(self.model)
            .values(**values)
            .on_conflict_do_nothing(constraint="uq_tg_update_bot_update_id")
            .returning(self.model.id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    def _bot_window(
        self,
        bot_id: UUID,
        since: datetime | None,
        until: datetime | None,
    ) -> list[Any]:
        """Build the common WHERE clause: bot scope + optional tg_date window."""
        conditions: list[Any] = [self.model.bot_id == bot_id]
        if since is not None:
            conditions.append(self.model.tg_date >= since)
        if until is not None:
            conditions.append(self.model.tg_date < until)
        return conditions

    async def count_by_type(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[str, int]]:
        """Count updates grouped by ``update_type`` for a bot."""
        stmt = (
            select(self.model.update_type, func.count())
            .where(*self._bot_window(bot_id, since, until))
            .group_by(self.model.update_type)
            .order_by(func.count().desc())
        )
        rows = (await session.execute(stmt)).all()
        return [(str(update_type), int(count)) for update_type, count in rows]

    async def count_by_content_type(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[str, int]]:
        """Count message-like updates grouped by ``content_type`` for a bot."""
        stmt = (
            select(self.model.content_type, func.count())
            .where(
                *self._bot_window(bot_id, since, until),
                self.model.content_type.is_not(None),
            )
            .group_by(self.model.content_type)
            .order_by(func.count().desc())
        )
        rows = (await session.execute(stmt)).all()
        return [(str(content_type), int(count)) for content_type, count in rows]

    async def timeseries(
        self,
        session: AsyncSession,
        bot_id: UUID,
        granularity: str = "day",
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[datetime, int]]:
        """Update volume bucketed by ``granularity`` (day/hour/week/month)."""
        bucket = func.date_trunc(granularity, self.model.tg_date)
        stmt = (
            select(bucket.label("bucket"), func.count())
            .where(
                *self._bot_window(bot_id, since, until),
                self.model.tg_date.is_not(None),
            )
            .group_by(bucket)
            .order_by(bucket)
        )
        rows = (await session.execute(stmt)).all()
        return [(bucket_value, int(count)) for bucket_value, count in rows]

    async def count_active_users(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> int:
        """Distinct Telegram users that produced any update in the window."""
        stmt = select(func.count(func.distinct(self.model.tg_user_id))).where(
            *self._bot_window(bot_id, since, until),
            self.model.tg_user_id.is_not(None),
        )
        return int((await session.execute(stmt)).scalar_one())

    async def count_by_chat_type(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[str, int]]:
        """Count updates grouped by Telegram ``chat_type`` (private/group/...)."""
        stmt = (
            select(self.model.chat_type, func.count())
            .where(
                *self._bot_window(bot_id, since, until),
                self.model.chat_type.is_not(None),
            )
            .group_by(self.model.chat_type)
            .order_by(func.count().desc())
        )
        rows = (await session.execute(stmt)).all()
        return [(str(chat_type), int(count)) for chat_type, count in rows]

    async def activity_heatmap(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[int, int, int]]:
        """Update volume per (weekday, hour) cell of ``tg_date`` in UTC.

        Weekday follows PostgreSQL's ``dow``: 0 is Sunday, 6 is Saturday.
        Only non-empty cells are returned.
        """
        weekday = func.extract("dow", self.model.tg_date)
        hour = func.extract("hour", self.model.tg_date)
        stmt = (
            select(weekday.label("weekday"), hour.label("hour"), func.count())
            .where(
                *self._bot_window(bot_id, since, until),
                self.model.tg_date.is_not(None),
            )
            .group_by("weekday", "hour")
            .order_by("weekday", "hour")
        )
        rows = (await session.execute(stmt)).all()
        return [
            (int(weekday_value), int(hour_value), int(count))
            for weekday_value, hour_value, count in rows
        ]

    async def top_users(
        self,
        session: AsyncSession,
        bot_id: UUID,
        limit: int = 10,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[int, int]]:
        """Most active Telegram users as ``(tg_user_id, update count)`` pairs."""
        stmt = (
            select(self.model.tg_user_id, func.count())
            .where(
                *self._bot_window(bot_id, since, until),
                self.model.tg_user_id.is_not(None),
            )
            .group_by(self.model.tg_user_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
        return [(int(tg_user_id), int(count)) for tg_user_id, count in rows]

    async def count_users_active_since(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime,
    ) -> int:
        """Distinct Telegram users with any update at or after ``since``."""
        return await self.count_active_users(session, bot_id, since=since)

    async def count_users_inactive_since(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime,
    ) -> int:
        """Users seen before ``since`` that produced no update after it.

        This is the churn counter: known users of the bot whose last activity
        predates the cutoff.
        """
        active = select(func.distinct(self.model.tg_user_id)).where(
            self.model.bot_id == bot_id,
            self.model.tg_user_id.is_not(None),
            self.model.tg_date >= since,
        )
        stmt = select(func.count(func.distinct(self.model.tg_user_id))).where(
            self.model.bot_id == bot_id,
            self.model.tg_user_id.is_not(None),
            self.model.tg_user_id.not_in(active),
        )
        return int((await session.execute(stmt)).scalar_one())
