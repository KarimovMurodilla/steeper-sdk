from uuid import UUID

from loggers import get_logger
from src.communication.enums import ChatStatus, MessageType, SenderType
from src.communication.schemas import BotMessagePayload
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
)
from src.core.schemas import SuccessResponse

logger = get_logger(__name__)


class LogBotMessageUseCase:
    """
    Use case for logging an outgoing bot message (from our frontend or from a
    bot middleware acting as a proxy).

    It performs the following steps:
    1. Resolves the bot by ``bot_id`` and validates the secret token (the bot's
       token hash) supplied in the request header.
    2. Resolves the chat for the Telegram user.
    3. Saves the Message (sender = bot).
    """

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
    ) -> None:
        self.uow = uow

    async def execute(
        self, bot_id: UUID, payload: BotMessagePayload, secret_token: str
    ) -> SuccessResponse:
        """
        Executes the business logic for logging a bot message.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            payload (BotMessagePayload): The message payload.
            secret_token (str): The bot's token hash, used to authenticate the
                request (compared against ``bot.token_hash``).

        Returns:
            SuccessResponse: A success confirmation response.

        Raises:
            InstanceNotFoundException: If the bot or telegram user is not found.
            AccessForbiddenException: If the secret token is invalid.
        """
        async with self.uow as uow:
            bot = await uow.bots.get_single(uow.session, id=bot_id)

            if not bot:
                logger.warning("Bot-message received for unknown bot_id: %s", bot_id)
                raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            if bot.token_hash != secret_token:
                logger.warning(
                    "Bot-message received with invalid secret token for bot: %s",
                    bot_id,
                )
                raise AccessForbiddenException(ErrorCode.AUTH_ACCESS_FORBIDDEN)

            if not bot.status == "active":
                logger.info("Webhook skipped for disabled bot: %s", bot.id)
                return SuccessResponse(success=True)

            tg_user = await uow.telegram_users.get_single(
                session=uow.session, tg_user_id=payload.chat_id, bot_id=bot.id
            )

            if not tg_user:
                logger.warning(
                    "Webhook received for unknown Telegram user: %s", payload.chat_id
                )
                raise InstanceNotFoundException(ErrorCode.AUTH_TELEGRAM_USER_NOT_FOUND)

            chat = await uow.chats.get_single(
                session=uow.session, bot_id=bot.id, telegram_user_id=tg_user.id
            )

            if not chat:
                chat = await uow.chats.create(
                    uow.session,
                    {
                        "bot_id": bot.id,
                        "telegram_user_id": payload.chat_id,
                        "status": ChatStatus.OPEN,
                    },
                )
                await uow.session.flush()

            msg_type = MessageType.TEXT  # TODO: Determine message type based on payload

            msg_data = {
                "chat_id": chat.id,
                "sender_type": SenderType.BOT,
                "message_type": msg_type,
                "tg_message_id": payload.message_id,
                "content": payload.text,
                "metadata_info": {
                    "tg_date": payload.date,
                },
            }

            await uow.messages.create(uow.session, msg_data)

            await uow.commit()
            logger.info(
                "Processed webhook for Bot %s, User %s, Msg %s",
                bot.id,
                payload.chat_id,
                payload.text,
            )

        return SuccessResponse(success=True)
