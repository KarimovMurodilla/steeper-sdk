"""Metrics dashboard router — mounted under /v1/bots."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.analytics.dependencies import (
    get_bot_audience_metrics_use_case,
    get_bot_traffic_metrics_use_case,
)
from src.analytics.schemas import (
    BotAudienceMetrics,
    BotTrafficMetrics,
    TimeGranularity,
)
from src.analytics.usecases.get_audience_metrics import GetBotAudienceMetricsUseCase
from src.analytics.usecases.get_traffic_metrics import GetBotTrafficMetricsUseCase
from src.bot.dependencies import require_bot
from src.bot.models import Bot

router = APIRouter()

GranularityQuery = Annotated[
    TimeGranularity, Query(description="Time-series bucket size")
]
SinceQuery = Annotated[
    datetime | None, Query(description="Inclusive start of the window")
]
UntilQuery = Annotated[
    datetime | None, Query(description="Exclusive end of the window")
]


@router.get(
    "/{bot_id}/metrics/traffic",
    response_model=BotTrafficMetrics,
    status_code=status.HTTP_200_OK,
)
async def get_bot_traffic_metrics(
    use_case: Annotated[
        GetBotTrafficMetricsUseCase, Depends(get_bot_traffic_metrics_use_case)
    ],
    bot: Annotated[Bot, Depends(require_bot)],
    granularity: GranularityQuery = TimeGranularity.DAY,
    since: SinceQuery = None,
    until: UntilQuery = None,
) -> BotTrafficMetrics:
    """
    Traffic panel: update and message volume, breakdowns by update, content,
    chat and sender type, a volume time-series, and a weekday/hour heatmap.
    """
    return await use_case.execute(
        bot_id=bot.id, granularity=granularity, since=since, until=until
    )


@router.get(
    "/{bot_id}/metrics/audience",
    response_model=BotAudienceMetrics,
    status_code=status.HTTP_200_OK,
)
async def get_bot_audience_metrics(
    use_case: Annotated[
        GetBotAudienceMetricsUseCase, Depends(get_bot_audience_metrics_use_case)
    ],
    bot: Annotated[Bot, Depends(require_bot)],
    granularity: GranularityQuery = TimeGranularity.DAY,
    since: SinceQuery = None,
    until: UntilQuery = None,
) -> BotAudienceMetrics:
    """
    Audience panel: total and new users, rolling DAU/WAU/MAU, churn, a growth
    time-series, the language mix, and the most active users.
    """
    return await use_case.execute(
        bot_id=bot.id, granularity=granularity, since=since, until=until
    )
