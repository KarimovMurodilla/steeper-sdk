from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from loggers import get_logger
from src.communication.models import Chat, Message
from src.core.database.repositories import BaseRepository

logger = get_logger(__name__)


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def get_cursor_paginated(
        self,
        session: AsyncSession,
        chat_id: UUID,
        limit: int = 50,
        cursor: UUID | None = None,
    ) -> list[Message]:
        """
        Cursor-based pagination using UUID7 ordering.
        Messages are returned newest-first (DESC).
        The cursor is the `id` of the last item from the previous page.
        """
        stmt = select(self.model).where(self.model.chat_id == chat_id)

        if cursor is not None:
            stmt = stmt.where(self.model.id < cursor)

        stmt = stmt.order_by(self.model.id.desc()).limit(limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_bot(self, session: AsyncSession, bot_id: UUID) -> int:
        """Total messages across all chats for a bot."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .join(Chat, Chat.id == self.model.chat_id)
            .where(Chat.bot_id == bot_id)
        )
        return int((await session.execute(stmt)).scalar_one())

    async def count_by_sender_type(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[str, int]]:
        """Message counts grouped by ``sender_type`` (inbound vs outbound)."""
        conditions: list[Any] = [Chat.bot_id == bot_id]
        if since is not None:
            conditions.append(self.model.created_at >= since)
        if until is not None:
            conditions.append(self.model.created_at < until)

        stmt = (
            select(self.model.sender_type, func.count())
            .select_from(self.model)
            .join(Chat, Chat.id == self.model.chat_id)
            .where(*conditions)
            .group_by(self.model.sender_type)
            .order_by(func.count().desc())
        )
        rows = (await session.execute(stmt)).all()
        return [(str(sender_type), int(count)) for sender_type, count in rows]
