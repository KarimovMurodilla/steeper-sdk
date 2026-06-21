"""Analytics summary router — mounted under /v1/bots."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.analytics.dependencies import (
    get_bot_analytics_summary_use_case,
    get_bot_update_stats_use_case,
)
from src.analytics.schemas import (
    BotAnalyticsSummary,
    BotUpdateStats,
    TimeGranularity,
)
from src.analytics.usecases.get_bot_summary import GetBotAnalyticsSummaryUseCase
from src.analytics.usecases.get_update_stats import GetBotUpdateStatsUseCase
from src.bot.dependencies import require_bot
from src.bot.models import Bot

router = APIRouter()


@router.get(
    "/{bot_id}/analytics/summary",
    response_model=BotAnalyticsSummary,
    status_code=status.HTTP_200_OK,
)
async def get_bot_analytics_summary(
    use_case: Annotated[
        GetBotAnalyticsSummaryUseCase,
        Depends(get_bot_analytics_summary_use_case),
    ],
    bot: Annotated[Bot, Depends(require_bot)],
) -> BotAnalyticsSummary:
    """
    Bot analytics summary: users, chats, messages, and daily active users.
    """
    return await use_case.execute(bot_id=bot.id)


@router.get(
    "/{bot_id}/analytics/updates",
    response_model=BotUpdateStats,
    status_code=status.HTTP_200_OK,
)
async def get_bot_update_stats(
    use_case: Annotated[
        GetBotUpdateStatsUseCase,
        Depends(get_bot_update_stats_use_case),
    ],
    bot: Annotated[Bot, Depends(require_bot)],
    granularity: Annotated[
        TimeGranularity, Query(description="Time-series bucket size")
    ] = TimeGranularity.DAY,
    since: Annotated[
        datetime | None, Query(description="Inclusive start of the window (tg_date)")
    ] = None,
    until: Annotated[
        datetime | None, Query(description="Exclusive end of the window (tg_date)")
    ] = None,
) -> BotUpdateStats:
    """
    Telegram update statistics for charts and filtering: totals, active users,
    breakdowns by update type and content type, and a volume time-series.
    """
    return await use_case.execute(
        bot_id=bot.id, granularity=granularity, since=since, until=until
    )
