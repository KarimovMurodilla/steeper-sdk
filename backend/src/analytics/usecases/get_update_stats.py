"""Use case: aggregate Telegram update statistics for a single bot."""

from datetime import datetime
from uuid import UUID

from src.analytics.schemas import (
    BotUpdateStats,
    LabeledCount,
    TimeBucketCount,
    TimeGranularity,
)
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork


class GetBotUpdateStatsUseCase:
    """
    Builds chart-ready statistics from the raw ``telegram_updates`` log.

    Aggregations (all scoped to one bot and an optional ``[since, until)``
    window over Telegram's own timestamp):
      - by_type:         update volume grouped by update type
      - by_content_type: message volume grouped by content type
      - timeseries:      update volume bucketed by the requested granularity
      - active_users:    distinct Telegram users seen in the window
    """

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(
        self,
        bot_id: UUID,
        granularity: TimeGranularity = TimeGranularity.DAY,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> BotUpdateStats:
        """
        Executes the business logic for the bot update statistics endpoint.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            granularity (TimeGranularity): Time-series bucket size.
            since (datetime | None): Inclusive lower bound on ``tg_date``.
            until (datetime | None): Exclusive upper bound on ``tg_date``.

        Returns:
            BotUpdateStats: Aggregated, chart-ready statistics.
        """
        async with self.uow as uow:
            by_type = await uow.telegram_updates.count_by_type(
                uow.session, bot_id, since, until
            )
            by_content = await uow.telegram_updates.count_by_content_type(
                uow.session, bot_id, since, until
            )
            series = await uow.telegram_updates.timeseries(
                uow.session, bot_id, granularity.value, since, until
            )
            active_users = await uow.telegram_updates.count_active_users(
                uow.session, bot_id, since, until
            )

        return BotUpdateStats(
            total=sum(count for _, count in by_type),
            active_users=active_users,
            by_type=[
                LabeledCount(label=label, count=count) for label, count in by_type
            ],
            by_content_type=[
                LabeledCount(label=label, count=count) for label, count in by_content
            ],
            timeseries=[
                TimeBucketCount(bucket=bucket, count=count) for bucket, count in series
            ],
        )
