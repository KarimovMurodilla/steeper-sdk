"""Use case: aggregate audience metrics for a single bot."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.analytics.schemas import (
    ActiveUserCounts,
    BotAudienceMetrics,
    LabeledCount,
    TimeBucketCount,
    TimeGranularity,
    TopUser,
)
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork

CHURN_DAYS = 30
TOP_USERS_LIMIT = 10


class GetBotAudienceMetricsUseCase:
    """
    Builds the audience panel of the metrics dashboard from existing tables.

    Growth (new users, language mix) and the top-user list honour the optional
    ``[since, until)`` window. The rolling DAU/WAU/MAU counters and the churn
    counter are always measured backwards from the current time, so they stay
    comparable regardless of the window the dashboard is showing.
    """

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(
        self,
        bot_id: UUID,
        granularity: TimeGranularity = TimeGranularity.DAY,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> BotAudienceMetrics:
        """
        Executes the business logic for the bot audience metrics endpoint.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            granularity (TimeGranularity): Time-series bucket size.
            since (datetime | None): Inclusive lower bound of the window.
            until (datetime | None): Exclusive upper bound of the window.

        Returns:
            BotAudienceMetrics: Aggregated, chart-ready audience statistics.
        """
        now = datetime.now(UTC)

        async with self.uow as uow:
            total_users = await uow.telegram_users.count_by_bot(uow.session, bot_id)
            new_series = await uow.telegram_users.new_users_timeseries(
                uow.session, bot_id, granularity.value, since, until
            )
            by_language = await uow.telegram_users.count_by_language(
                uow.session, bot_id, since, until
            )
            dau = await uow.telegram_updates.count_users_active_since(
                uow.session, bot_id, now - timedelta(days=1)
            )
            wau = await uow.telegram_updates.count_users_active_since(
                uow.session, bot_id, now - timedelta(days=7)
            )
            mau = await uow.telegram_updates.count_users_active_since(
                uow.session, bot_id, now - timedelta(days=CHURN_DAYS)
            )
            churned = await uow.telegram_updates.count_users_inactive_since(
                uow.session, bot_id, now - timedelta(days=CHURN_DAYS)
            )
            top = await uow.telegram_updates.top_users(
                uow.session, bot_id, TOP_USERS_LIMIT, since, until
            )
            names = await uow.telegram_users.get_display_names(
                uow.session, bot_id, [tg_user_id for tg_user_id, _ in top]
            )

        return BotAudienceMetrics(
            total_users=total_users,
            new_users=sum(count for _, count in new_series),
            active=ActiveUserCounts(dau=dau, wau=wau, mau=mau),
            churned_users=churned,
            new_users_timeseries=[
                TimeBucketCount(bucket=bucket, count=count)
                for bucket, count in new_series
            ],
            by_language=[
                LabeledCount(label=label, count=count) for label, count in by_language
            ],
            top_users=[
                TopUser(
                    tg_user_id=tg_user_id,
                    first_name=names.get(tg_user_id, (None, None))[0],
                    username=names.get(tg_user_id, (None, None))[1],
                    updates=count,
                )
                for tg_user_id, count in top
            ],
        )
