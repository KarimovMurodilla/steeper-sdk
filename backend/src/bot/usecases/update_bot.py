from uuid import UUID

from loggers import get_logger
from src.bot.schemas import BotUpdateRequest, BotViewModel
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import CoreException, InstanceNotFoundException
from src.core.utils.encryption import encrypt_token
from src.core.utils.security import hash_token
from src.integrations.telegram.bot.telegram_bot_api import TelegramBotAPIService

logger = get_logger(__name__)


class UpdateBotUseCase:
    """Use case for updating a Telegram Bot's settings."""

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
        tg_service: TelegramBotAPIService,
    ) -> None:
        self.uow = uow
        self.tg_service = tg_service

    async def execute(
        self,
        bot_id: UUID,
        data: BotUpdateRequest,
    ) -> BotViewModel:
        """
        Executes the business logic for updating an existing Telegram Bot.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            data (BotUpdateRequest): The payload containing updated bot details.

        Returns:
            BotViewModel: The updated bot details.

        Raises:
            InstanceNotFoundException: If the bot is not found.
            CoreException: If the new bot token is invalid.
        """
        async with self.uow as uow:
            bot = await uow.bots.get_single(uow.session, id=bot_id)
            if not bot:
                raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            update_data = data.model_dump(exclude_unset=True)

            if data.token:
                bot_info = await self.tg_service.get_me(data.token)
                if not bot_info:
                    raise CoreException(ErrorCode.AUTH_TOKEN_INVALID)

                token_hash = hash_token(data.token)
                token_encrypted = encrypt_token(data.token)

                update_data["token_hash"] = token_hash
                update_data["token_encrypted"] = token_encrypted

                update_data["name"] = bot_info.first_name
                update_data["username"] = bot_info.username
                del update_data["token"]

            if update_data:
                bot = await uow.bots.update(uow.session, update_data, id=bot_id)
                if bot is None:
                    raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            result = BotViewModel.model_validate(bot)

        logger.info(f"Bot updated successfully: {result.id}")
        return result
