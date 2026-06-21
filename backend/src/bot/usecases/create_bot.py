from uuid import UUID

from loggers import get_logger
from src.bot.schemas import BotCreateRequest, BotViewModel
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import CoreException
from src.core.utils.encryption import encrypt_token
from src.core.utils.security import hash_token
from src.integrations.telegram.bot.telegram_bot_api import TelegramBotAPIService
from src.main.config import config

logger = get_logger(__name__)


class CreateBotUseCase:
    """Use case for creating a new Telegram Bot."""

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
        tg_service: TelegramBotAPIService,
    ) -> None:
        self.uow = uow
        self.tg_service = tg_service

    async def _set_webhook(self, token: str, bot_id: UUID) -> bool:
        webhook_url = (
            f"{config.telegram.TELEGRAM_WEBHOOK_URL}/v1/communications/webhook/{bot_id}"
        )
        token_hash = hash_token(token)
        return await self.tg_service.set_webhook(
            token=token,
            url=webhook_url,
            secret_token=token_hash,
        )

    async def execute(
        self,
        data: BotCreateRequest,
        created_by_user_id: UUID,
    ) -> BotViewModel:
        """
        Executes the business logic for creating a new Telegram Bot.

        Args:
            data (BotCreateRequest): The payload containing bot details.
            created_by_user_id (UUID): User creating the bot (for log output).

        Returns:
            BotViewModel: The created bot details.

        Raises:
            CoreException: If the provided bot token is invalid.
        """
        bot_info = await self.tg_service.get_me(data.token)
        if not bot_info:
            raise CoreException(ErrorCode.AUTH_TOKEN_INVALID)

        async with self.uow as uow:
            token_hash = hash_token(data.token)
            token_encrypted = encrypt_token(data.token)

            bot_data = {
                "name": bot_info.first_name,
                "token_hash": token_hash,
                "token_encrypted": token_encrypted,
                "username": bot_info.username,
            }

            new_bot = await uow.bots.create(uow.session, bot_data)

            await uow.session.flush()

            result = BotViewModel.model_validate(new_bot)

            await uow.commit()

        is_webhook_set = await self._set_webhook(data.token, result.id)
        if not is_webhook_set:
            logger.warning(f"Webhook setup failed for bot {result.id}")
        else:
            logger.info(f"Webhook set successfully for bot {result.id}")

        await self.tg_service.set_chat_menu_button(
            token=data.token,
            chat_id=875587704,
            url=f"{config.telegram.TELEGRAM_WEBHOOK_URL}?bot_id={result.id}",
            text="Open Web App Dude",
        )

        logger.info(
            f"Bot created successfully: {result.id} by user {created_by_user_id}"
        )

        return result
