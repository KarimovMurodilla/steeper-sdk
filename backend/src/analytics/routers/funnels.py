"""Funnel routers.

Two routers, because the two sides authenticate differently — the same split as
the bot-logs module:

* ``ingest_router`` is mounted next to the Telegram webhook and is called by the
  ``steeper`` client library, authenticating with the bot's ``token_hash`` in
  the ``x-telegram-bot-api-secret-token`` header.
* ``router`` is mounted under ``/v1/bots`` and serves the operator panel, behind
  the usual JWT auth.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from src.analytics.dependencies import (
    get_create_funnel_use_case,
    get_delete_funnel_use_case,
    get_funnel_report_use_case,
    get_funnel_use_case,
    get_ingest_bot_events_use_case,
    get_list_event_names_use_case,
    get_list_funnels_use_case,
    get_update_funnel_use_case,
)
from src.analytics.routers.metrics import SinceQuery, UntilQuery
from src.analytics.schemas import (
    BotEventBatchPayload,
    EventName,
    FunnelCreate,
    FunnelReport,
    FunnelUpdate,
    FunnelViewModel,
)
from src.analytics.usecases.get_funnel_report import GetFunnelReportUseCase
from src.analytics.usecases.ingest_events import IngestBotEventsUseCase
from src.analytics.usecases.list_event_names import ListEventNamesUseCase
from src.analytics.usecases.manage_funnels import (
    CreateFunnelUseCase,
    DeleteFunnelUseCase,
    GetFunnelUseCase,
    ListFunnelsUseCase,
    UpdateFunnelUseCase,
)
from src.bot.dependencies import require_bot
from src.bot.models import Bot
from src.core.schemas import SuccessResponse
from src.user.auth.dependencies import get_current_user
from src.user.models import User

ingest_router = APIRouter()
router = APIRouter()


@ingest_router.post(
    "/{bot_id}/events",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
    responses={
        400: {"description": "Invalid payload format"},
        403: {"description": "Invalid Telegram secret token"},
        404: {"description": "Bot not found"},
    },
)
async def ingest_bot_events(
    bot_id: UUID,
    payload: BotEventBatchPayload,
    use_case: Annotated[
        IngestBotEventsUseCase, Depends(get_ingest_bot_events_use_case)
    ],
    x_telegram_bot_api_secret_token: Annotated[str, Header()] = "",
) -> SuccessResponse:
    """
    Accepts a batch of product events reported by a bot process.

    These are the steps that never appear in Telegram traffic — "pressed the
    pricing button", "finished onboarding", "paid" — and they are what funnels
    are built from.

    The bot is identified by ``bot_id`` in the path and authenticated with the
    secret token (SHA-256 of the bot token) in the
    ``x-telegram-bot-api-secret-token`` header, the same scheme as the incoming
    webhook and log endpoints.

    Events timestamped more than an hour in the future are dropped rather than
    stored: a badly skewed bot clock would reorder that user's funnel steps.
    """
    return await use_case.execute(bot_id, payload, x_telegram_bot_api_secret_token)


@router.get(
    "/{bot_id}/events/names",
    response_model=list[EventName],
    status_code=status.HTTP_200_OK,
)
async def list_event_names(
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[ListEventNamesUseCase, Depends(get_list_event_names_use_case)],
) -> list[EventName]:
    """
    Lists the event names this bot has actually sent, busiest first.

    The funnel builder offers these as suggestions, so a step cannot be named
    after an event that never existed — a mistake that otherwise produces a
    flat zero indistinguishable from genuine non-conversion.
    """
    return await use_case.execute(bot.id)


@router.get(
    "/{bot_id}/funnels",
    response_model=list[FunnelViewModel],
    status_code=status.HTTP_200_OK,
)
async def list_funnels(
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[ListFunnelsUseCase, Depends(get_list_funnels_use_case)],
) -> list[FunnelViewModel]:
    """Lists this bot's funnel definitions, newest first."""
    return await use_case.execute(bot.id)


@router.post(
    "/{bot_id}/funnels",
    response_model=FunnelViewModel,
    status_code=status.HTTP_201_CREATED,
)
async def create_funnel(
    payload: FunnelCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[CreateFunnelUseCase, Depends(get_create_funnel_use_case)],
) -> FunnelViewModel:
    """
    Defines a funnel: an ordered list of event names plus a conversion window.

    Repeating a step name is allowed and means "did it again after the previous
    step". The window is measured from the first step, so it bounds the whole
    journey rather than each hop.
    """
    return await use_case.execute(bot.id, payload)


@router.get(
    "/{bot_id}/funnels/{funnel_id}",
    response_model=FunnelViewModel,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Funnel not found"}},
)
async def get_funnel(
    funnel_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[GetFunnelUseCase, Depends(get_funnel_use_case)],
) -> FunnelViewModel:
    """Reads one funnel definition."""
    return await use_case.execute(bot.id, funnel_id)


@router.patch(
    "/{bot_id}/funnels/{funnel_id}",
    response_model=FunnelViewModel,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Funnel not found"}},
)
async def update_funnel(
    funnel_id: UUID,
    payload: FunnelUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[UpdateFunnelUseCase, Depends(get_update_funnel_use_case)],
) -> FunnelViewModel:
    """Applies a partial update to a funnel definition."""
    return await use_case.execute(bot.id, funnel_id, payload)


@router.delete(
    "/{bot_id}/funnels/{funnel_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Funnel not found"}},
)
async def delete_funnel(
    funnel_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[DeleteFunnelUseCase, Depends(get_delete_funnel_use_case)],
) -> SuccessResponse:
    """Soft-deletes a funnel definition. Its events are untouched."""
    return await use_case.execute(bot.id, funnel_id)


@router.get(
    "/{bot_id}/funnels/{funnel_id}/report",
    response_model=FunnelReport,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Window or stored definition out of bounds"},
        404: {"description": "Funnel not found"},
    },
)
async def get_funnel_report(
    funnel_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    bot: Annotated[Bot, Depends(require_bot)],
    use_case: Annotated[GetFunnelReportUseCase, Depends(get_funnel_report_use_case)],
    since: SinceQuery = None,
    until: UntilQuery = None,
    mature_only: Annotated[
        bool,
        Query(
            description=(
                "Admit only entrants who have had a full conversion window, "
                "by pulling the entry window's end back by window_seconds. Off "
                "by default because it hides the most recent cohort entirely."
            )
        ),
    ] = False,
    include_timings: Annotated[
        bool,
        Query(
            description=(
                "Compute the median time between steps. Turning it off skips "
                "one sort per step, which matters on very large windows."
            )
        ),
    ] = True,
) -> FunnelReport:
    """
    Computes the funnel over ``[since, until)``.

    Per user, the first occurrence of the first step inside the window opens
    the funnel; each later step is that user's earliest matching event after
    the previous one and within the conversion window of the *first* step.

    Later steps are deliberately not clipped at ``until`` — a user who entered
    just before it may still convert afterwards, and clipping would report a
    fake zero for the most recent cohort. Use ``mature_only`` when a fully
    settled number matters more than a current one.

    Conversions and medians are null, never zero, where there is no data to
    divide by.
    """
    return await use_case.execute(
        bot_id=bot.id,
        funnel_id=funnel_id,
        since=since,
        until=until,
        mature_only=mature_only,
        include_timings=include_timings,
    )
