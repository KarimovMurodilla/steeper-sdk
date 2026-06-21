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
