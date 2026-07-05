import time
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
from src.core.utils.security import verify_secret_token
from src.realtime.broker import broker, steeper_exchange
from src.realtime.enums import EventType
from src.realtime.schemas import WSChatMessageCreatedData, WSDownlinkEnvelope

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

            if not verify_secret_token(bot.token_hash, secret_token):
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
                        "telegram_user_id": tg_user.id,
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

            new_message = await uow.messages.create(uow.session, msg_data)

            await uow.session.flush()
            await uow.commit()

            # Capture as primitives before leaving the transaction so the
            # publish below never touches a detached/expired ORM instance.
            bot_id_str = str(bot.id)
            chat_id_str = str(chat.id)
            message_id_str = str(new_message.id)

            logger.info(
                "Processed webhook for Bot %s, User %s, Msg %s",
                bot.id,
                payload.chat_id,
                payload.text,
            )

        # Broadcast the outgoing bot message so connected clients see it in
        # real time, mirroring the incoming-webhook and admin-send paths.
        routing_key = f"bot.{bot_id_str}.chat.{chat_id_str}.message.created"
        message_data = WSChatMessageCreatedData(
            message_id=message_id_str,
            tg_message_id=payload.message_id,
            text=payload.text,
            sender_type=SenderType.BOT,
        )
        envelope = WSDownlinkEnvelope(
            version=1,
            event=EventType.CHAT_MESSAGE_CREATED,
            bot_id=bot_id_str,
            chat_id=chat_id_str,
            timestamp=int(time.time()),
            data=message_data.model_dump(mode="json"),
        )
        try:
            await broker.publish(
                envelope.model_dump(mode="json"),
                routing_key=routing_key,
                exchange=steeper_exchange,
            )
            logger.debug(
                "Published %s event to %s", EventType.CHAT_MESSAGE_CREATED, routing_key
            )
        except Exception as e:
            logger.exception(
                "Failed to publish CHAT_MESSAGE_CREATED event to RabbitMQ: %s", e
            )

        return SuccessResponse(success=True)
