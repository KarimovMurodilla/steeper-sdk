from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.models import Bot
from src.bot.repositories.bot import BotRepository
from src.bot.services.bot import BotService
from src.bot.usecases.create_bot import CreateBotUseCase
from src.bot.usecases.delete_bot import DeleteBotUseCase
from src.bot.usecases.update_bot import UpdateBotUseCase
from src.core.database.session import get_session, get_unit_of_work
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import InstanceNotFoundException
from src.integrations.telegram.bot.telegram_bot_api import TelegramBotAPIService
from src.integrations.telegram.dependencies import get_telegram_bot_api_service


async def require_bot(
    bot_id: Annotated[UUID, Path(..., description="Bot ID")],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Bot:
    """Load the bot from the path or 404."""
    bot = await session.get(Bot, bot_id)
    if not bot:
        raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)
    return bot


async def get_bot_service() -> BotService:
    """
    Dependency to get the BotService.
    """
    repo = BotRepository()
    return BotService(repository=repo)


def get_create_bot_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
    tg_service: TelegramBotAPIService = Depends(get_telegram_bot_api_service),
) -> CreateBotUseCase:
    return CreateBotUseCase(uow=uow, tg_service=tg_service)


def get_update_bot_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
    tg_service: TelegramBotAPIService = Depends(get_telegram_bot_api_service),
) -> UpdateBotUseCase:
    return UpdateBotUseCase(uow=uow, tg_service=tg_service)


def get_delete_bot_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
    tg_service: TelegramBotAPIService = Depends(get_telegram_bot_api_service),
) -> DeleteBotUseCase:
    return DeleteBotUseCase(uow=uow, tg_service=tg_service)
