"""Chat subdomain router — mounted at /v1/bots so bot_id is in the path."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.bot.dependencies import require_bot
from src.bot.models import Bot
from src.communication.chat.usecases.list_chats import ListChatsUseCase
from src.communication.chat.usecases.list_messages import ListMessagesUseCase
from src.communication.chat.usecases.send_message import SendMessageUseCase
from src.communication.dependencies import (
    get_list_chats_use_case,
    get_list_messages_use_case,
    get_send_message_use_case,
)
from src.communication.schemas import (
    ChatListItemViewModel,
    CursorPaginatedResponse,
    MessageListItemViewModel,
    SendMessageRequest,
    SendMessageResponse,
)
from src.core.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get(
    "/{bot_id}/chats",
    response_model=PaginatedResponse[ChatListItemViewModel],
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Bot not found"},
    },
)
async def list_bot_chats(
    pagination: Annotated[PaginationParams, Depends()],
    use_case: Annotated[ListChatsUseCase, Depends(get_list_chats_use_case)],
    bot: Annotated[Bot, Depends(require_bot)],
) -> PaginatedResponse[ChatListItemViewModel]:
    """
    List all chats for a bot with last message preview.
    """
    return await use_case.execute(bot_id=bot.id, pagination=pagination)


@router.get(
    "/{bot_id}/chats/{chat_id}/messages",
    response_model=CursorPaginatedResponse[MessageListItemViewModel],
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Bot or Chat not found"},
    },
)
async def list_messages(
    chat_id: UUID,
    use_case: Annotated[ListMessagesUseCase, Depends(get_list_messages_use_case)],
    bot: Annotated[Bot, Depends(require_bot)],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: UUID | None = Query(default=None),
) -> CursorPaginatedResponse[MessageListItemViewModel]:
    """
    Cursor-paginated message history for a chat.
    """
    return await use_case.execute(chat_id=chat_id, limit=limit, cursor=cursor)


@router.post(
    "/{bot_id}/chats/{chat_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid payload format"},
        403: {"description": "Permission denied"},
        404: {"description": "Bot or Chat not found"},
    },
)
async def send_message(
    chat_id: UUID,
    data: SendMessageRequest,
    use_case: Annotated[SendMessageUseCase, Depends(get_send_message_use_case)],
    bot: Annotated[Bot, Depends(require_bot)],
) -> SendMessageResponse:
    """
    Send a text message to the Telegram user through the bot.
    """
    return await use_case.execute(chat_id=chat_id, data=data)
