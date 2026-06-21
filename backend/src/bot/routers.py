from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.dependencies import (
    get_bot_service,
    get_create_bot_use_case,
    get_delete_bot_use_case,
    get_update_bot_use_case,
    require_bot,
)
from src.bot.models import Bot
from src.bot.schemas import BotCreateRequest, BotUpdateRequest, BotViewModel
from src.bot.services.bot import BotService
from src.bot.usecases.create_bot import CreateBotUseCase
from src.bot.usecases.delete_bot import DeleteBotUseCase
from src.bot.usecases.update_bot import UpdateBotUseCase
from src.core.database.session import get_session
from src.core.pagination import PaginatedResponse, PaginationParams
from src.user.auth.dependencies import get_current_user
from src.user.models import User

router = APIRouter()


@router.post(
    "/",
    response_model=BotViewModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid payload"},
        403: {"description": "Permission denied"},
        409: {"description": "Conflict (e.g., bot exists)"},
    },
)
async def create_bot(
    bot_data: BotCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateBotUseCase, Depends(get_create_bot_use_case)],
) -> BotViewModel:
    """
    Creates a new bot.
    """
    return await use_case.execute(data=bot_data, created_by_user_id=current_user.id)


@router.get(
    "/",
    response_model=PaginatedResponse[BotViewModel],
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
    },
)
async def get_bots(
    current_user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[PaginationParams, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    bot_service: Annotated[BotService, Depends(get_bot_service)],
) -> PaginatedResponse[BotViewModel]:
    """
    Lists all bots.
    """
    return await bot_service.get_paginated_list(session=session, pagination=pagination)


@router.patch(
    "/{bot_id}",
    response_model=BotViewModel,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid payload"},
        403: {"description": "Permission denied"},
        404: {"description": "Bot not found"},
        409: {"description": "Conflict on update"},
    },
)
async def update_bot(
    data: BotUpdateRequest,
    use_case: Annotated[UpdateBotUseCase, Depends(get_update_bot_use_case)],
    bot: Annotated[Bot, Depends(require_bot)],
) -> BotViewModel:
    """
    Update a bot's settings.
    """
    return await use_case.execute(bot_id=bot.id, data=data)


@router.delete(
    "/{bot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Bot not found"},
    },
)
async def delete_bot(
    use_case: Annotated[DeleteBotUseCase, Depends(get_delete_bot_use_case)],
    bot: Annotated[Bot, Depends(require_bot)],
) -> None:
    """
    Delete a bot.
    """
    await use_case.execute(bot_id=bot.id)
