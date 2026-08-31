"""Bot system logs routers.

Two separate routers, because the two sides authenticate differently:

* ``ingest_router`` is mounted next to the Telegram webhook and is called by the
  ``steeper`` client library — it authenticates with the bot's ``token_hash`` in
  the ``x-telegram-bot-api-secret-token`` header, like the webhook endpoints.
* ``router`` is mounted under ``/v1/bots`` and serves the operator panel, behind
  the usual JWT auth.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status

from src.bot.dependencies import require_bot
from src.bot.models import Bot
from src.communication.schemas import CursorPaginatedResponse
from src.core.schemas import SuccessResponse
from src.system.logs.dependencies import (
    get_ingest_bot_logs_use_case,
    get_list_bot_logs_use_case,
)
from src.system.logs.enums import LogLevel
from src.system.logs.schemas import BotLogBatchPayload, BotLogViewModel
from src.system.logs.usecases.ingest_logs import IngestBotLogsUseCase
from src.system.logs.usecases.list_logs import ListBotLogsUseCase
from src.user.auth.dependencies import get_current_user
from src.user.models import User

ingest_router = APIRouter()
router = APIRouter()


@ingest_router.post(
    "/{bot_id}/logs",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse,
    responses={
        400: {"description": "Invalid payload format"},
        403: {"description": "Invalid Telegram secret token"},
        404: {"description": "Bot not found"},
        500: {"description": "Log storage unavailable"},
    },
)
async def ingest_bot_logs(
    bot_id: UUID,
    payload: BotLogBatchPayload,
    use_case: Annotated[IngestBotLogsUseCase, Depends(get_ingest_bot_logs_use_case)],
    x_telegram_bot_api_secret_token: Annotated[str, Header()] = "",
) -> SuccessResponse:
    """
    Accepts a batch of `logging` records captured inside a bot process.

    The bot is identified by ``bot_id`` in the path and authenticated with the
    secret token (SHA-256 of the bot token) in the
    ``x-telegram-bot-api-secret-token`` header — the same scheme as the incoming
    webhook endpoint.

    Records are pushed to Loki and the whole batch is forwarded to operator
    panels subscribed to this bot's log stream.
    """
    return await use_case.execute(bot_id, payload, x_telegram_bot_api_secret_token)


@router.get(
    "/{bot_id}/logs",
    response_model=CursorPaginatedResponse[BotLogViewModel],
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Bot not found"},
        500: {"description": "Log storage unavailable"},
    },
)
async def list_bot_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListBotLogsUseCase, Depends(get_list_bot_logs_use_case)],
    bot: Annotated[Bot, Depends(require_bot)],
    limit: int = Query(default=100, ge=1, le=500),
    cursor: str | None = Query(
        default=None,
        description="Unix-nanosecond timestamp of the last item of the previous page",
    ),
    level: Annotated[list[LogLevel] | None, Query()] = None,
    logger_name: str | None = Query(default=None, max_length=255),
    search: str | None = Query(default=None, max_length=255),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> CursorPaginatedResponse[BotLogViewModel]:
    """
    Cursor-paginated log history for a bot, newest first.

    History is what the panel loads on open and when scrolling back; new records
    arrive over the WebSocket instead.
    """
    return await use_case.execute(
        bot_id=bot.id,
        limit=limit,
        cursor=cursor,
        levels=level,
        logger_name=logger_name,
        search=search,
        since=since,
        until=until,
    )
