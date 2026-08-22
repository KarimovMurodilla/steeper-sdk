"""Use case: aggregate traffic metrics for a single bot."""

from datetime import datetime
from uuid import UUID

from src.analytics.schemas import (
    BotTrafficMetrics,
    HeatmapCell,
    LabeledCount,
    TimeBucketCount,
    TimeGranularity,
)
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork


class GetBotTrafficMetricsUseCase:
    """
    Builds the traffic panel of the metrics dashboard from existing tables.

    Volume aggregations are scoped to one bot and an optional ``[since, until)``
    window. Update-based ones use Telegram's own ``tg_date``; the message
    breakdown uses our own ``created_at``, since stored messages carry no
    Telegram timestamp of their own. ``total_chats`` and ``all_time_messages``
    are lifetime totals and ignore the window.
    """

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(
        self,
        bot_id: UUID,
        granularity: TimeGranularity = TimeGranularity.DAY,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> BotTrafficMetrics:
        """
        Executes the business logic for the bot traffic metrics endpoint.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            granularity (TimeGranularity): Time-series bucket size.
            since (datetime | None): Inclusive lower bound of the window.
            until (datetime | None): Exclusive upper bound of the window.

        Returns:
            BotTrafficMetrics: Aggregated, chart-ready traffic statistics.
        """
        async with self.uow as uow:
            by_update_type = await uow.telegram_updates.count_by_type(
                uow.session, bot_id, since, until
            )
            by_content_type = await uow.telegram_updates.count_by_content_type(
                uow.session, bot_id, since, until
            )
            by_chat_type = await uow.telegram_updates.count_by_chat_type(
                uow.session, bot_id, since, until
            )
            by_sender_type = await uow.messages.count_by_sender_type(
                uow.session, bot_id, since, until
            )
            series = await uow.telegram_updates.timeseries(
                uow.session, bot_id, granularity.value, since, until
            )
            heatmap = await uow.telegram_updates.activity_heatmap(
                uow.session, bot_id, since, until
            )
            total_chats = await uow.chats.count_by_bot(uow.session, bot_id)
            all_time_messages = await uow.messages.count_by_bot(uow.session, bot_id)

        return BotTrafficMetrics(
            total_updates=sum(count for _, count in by_update_type),
            total_messages=sum(count for _, count in by_sender_type),
            total_chats=total_chats,
            all_time_messages=all_time_messages,
            by_update_type=[
                LabeledCount(label=label, count=count)
                for label, count in by_update_type
            ],
            by_content_type=[
                LabeledCount(label=label, count=count)
                for label, count in by_content_type
            ],
            by_chat_type=[
                LabeledCount(label=label, count=count) for label, count in by_chat_type
            ],
            by_sender_type=[
                LabeledCount(label=label, count=count)
                for label, count in by_sender_type
            ],
            timeseries=[
                TimeBucketCount(bucket=bucket, count=count) for bucket, count in series
            ],
            heatmap=[
                HeatmapCell(weekday=weekday, hour=hour, count=count)
                for weekday, hour, count in heatmap
            ],
        )
