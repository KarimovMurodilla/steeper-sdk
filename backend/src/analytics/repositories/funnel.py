"""Storage for funnel definitions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.models import Funnel
from src.core.database.repositories import SoftDeleteRepository


class FunnelRepository(SoftDeleteRepository[Funnel]):
    model = Funnel

    async def list_for_bot(self, session: AsyncSession, bot_id: UUID) -> list[Funnel]:
        """Return a bot's funnels, newest first."""
        stmt = (
            select(self.model)
            .where(self.model.bot_id == bot_id, self.model.is_deleted.is_(False))
            .order_by(self.model.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
