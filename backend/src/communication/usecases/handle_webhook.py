import time
from typing import Any
from uuid import UUID

from loggers import get_logger
from src.communication.enums import (
    ChatStatus,
    ContentType,
    MessageType,
    SenderType,
    UpdateType,
)
from src.communication.schemas import TelegramUpdatePayload
from src.communication.services.telegram_update_classifier import (
    ClassifiedUpdate,
    classify_update,
)
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
)
from src.core.schemas import SuccessResponse
from src.realtime.broker import broker, steeper_exchange
from src.realtime.enums import EventType
from src.realtime.schemas import (
    WSChatCreatedData,
    WSChatMessageCreatedData,
    WSDownlinkEnvelope,
)

logger = get_logger(__name__)

# Telegram message content -> our coarse MessageType bucket.
_CONTENT_TO_MESSAGE_TYPE: dict[ContentType, MessageType] = {
    ContentType.TEXT: MessageType.TEXT,
    ContentType.PHOTO: MessageType.IMAGE,
    ContentType.VIDEO: MessageType.VIDEO,
    ContentType.VIDEO_NOTE: MessageType.VIDEO,
    ContentType.ANIMATION: MessageType.VIDEO,
    ContentType.VOICE: MessageType.AUDIO,
    ContentType.AUDIO: MessageType.AUDIO,
    ContentType.DOCUMENT: MessageType.DOCUMENT,
    ContentType.SERVICE: MessageType.SYSTEM,
}

# Update types that we turn into Chat/Message domain objects.
_PROCESSABLE_MESSAGE_TYPES = frozenset(
    {UpdateType.MESSAGE, UpdateType.EDITED_MESSAGE}
)


class HandleWebhookUseCase:
    """
    Use case for processing incoming webhooks from Telegram or Middleware.

    Every incoming update is stored verbatim in ``telegram_updates`` (with flat
    analytics dimensions extracted on ingest) so that no data is ever lost —
    including update types we do not yet act on. On top of that raw log, plain
    message updates additionally drive the chat workflow:
    1. Validates the bot token hash.
    2. Persists the raw update (idempotent against Telegram retries).
    3. For message updates: upserts the Telegram User (CRM), gets/creates the
       Chat, saves the Message, and publishes real-time events.
    """

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
    ) -> None:
        self.uow = uow

    async def _publish_chat_created(
        self,
        bot_id_str: str,
        chat_id_str: str,
        tg_user_data: dict[str, Any],
    ) -> None:
        """Publishes an event notifying that a new chat was created."""
        routing_key = f"bot.{bot_id_str}.chat.{chat_id_str}.created"

        chat_data = WSChatCreatedData(
            chat_id=chat_id_str,
            telegram_user=tg_user_data,
            status=ChatStatus.OPEN,
        )
        envelope = WSDownlinkEnvelope(
            version=1,
            event=EventType.CHAT_CREATED,
            bot_id=bot_id_str,
            chat_id=chat_id_str,
            timestamp=int(time.time()),
            data=chat_data.model_dump(mode="json"),
        )
        try:
            await broker.publish(
                envelope.model_dump(mode="json"),
                routing_key=routing_key,
                exchange=steeper_exchange,
            )
            logger.debug(
                "Published %s event to %s", EventType.CHAT_CREATED, routing_key
            )
        except Exception as e:
            logger.exception("Failed to publish CHAT_CREATED event to RabbitMQ: %s", e)

    async def _publish_message_created(
        self,
        bot_id_str: str,
        chat_id_str: str,
        message_id_str: str,
        tg_message_id: int,
        content: str,
        sender_type: SenderType,
    ) -> None:
        """Publishes an event notifying that a new message was received."""
        routing_key = f"bot.{bot_id_str}.chat.{chat_id_str}.message.created"
        message_data = WSChatMessageCreatedData(
            message_id=message_id_str,
            tg_message_id=tg_message_id,
            text=content,
            sender_type=sender_type,
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

    async def execute(
        self,
        bot_id: UUID,
        payload: TelegramUpdatePayload,
        raw: dict[str, Any],
        secret_token: str,
    ) -> SuccessResponse:
        """
        Executes the business logic for handling an incoming webhook update.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            payload (TelegramUpdatePayload): The parsed webhook payload (used for
                the message workflow).
            raw (dict[str, Any]): The full, verbatim update body to be stored.
            secret_token (str): The security token to validate the request.

        Returns:
            SuccessResponse: A success confirmation response.

        Raises:
            InstanceNotFoundException: If the bot is not found.
            AccessForbiddenException: If the secret token is invalid.
        """
        classified = classify_update(raw)
        logger.info(
            "Received update %s (type=%s) for bot %s",
            payload.update_id,
            classified.update_type,
            bot_id,
        )

        typed_msg = payload.message or payload.edited_message
        process_as_message = (
            classified.update_type in _PROCESSABLE_MESSAGE_TYPES
            and typed_msg is not None
            and typed_msg.from_user is not None
        )

        async with self.uow as uow:
            bot = await uow.bots.get_single(uow.session, id=bot_id)

            if not bot:
                logger.warning("Webhook received for unknown bot_id: %s", bot_id)
                raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            if bot.token_hash != secret_token:
                logger.warning(
                    "Webhook received with invalid secret token for bot: %s", bot_id
                )
                raise AccessForbiddenException(ErrorCode.AUTH_ACCESS_FORBIDDEN)

            # Persist the raw update first. Idempotent on (bot_id, update_id) so
            # Telegram's retries never create duplicates or reprocess a message.
            is_new_update = await uow.telegram_updates.record(
                uow.session,
                {
                    "bot_id": bot.id,
                    "update_id": payload.update_id,
                    "update_type": classified.update_type,
                    "tg_user_id": classified.tg_user_id,
                    "tg_chat_id": classified.tg_chat_id,
                    "chat_type": classified.chat_type,
                    "content_type": classified.content_type,
                    "tg_date": classified.tg_date,
                    "processed": process_as_message and bot.status == "active",
                    "raw": raw,
                },
            )

            if not is_new_update:
                logger.info(
                    "Duplicate update %s for bot %s; skipping processing",
                    payload.update_id,
                    bot.id,
                )
                await uow.commit()
                return SuccessResponse(success=True)

            if bot.status != "active":
                logger.info(
                    "Update %s stored; processing skipped for disabled bot %s",
                    payload.update_id,
                    bot.id,
                )
                await uow.commit()
                return SuccessResponse(success=True)

            if not process_as_message or typed_msg is None or typed_msg.from_user is None:
                logger.debug(
                    "Stored %s update %s; no message workflow to run",
                    classified.update_type,
                    payload.update_id,
                )
                await uow.commit()
                return SuccessResponse(success=True)

            tg_user_data = typed_msg.from_user.model_dump(by_alias=True)
            db_user = await uow.telegram_users.upsert(uow.session, bot.id, tg_user_data)
            chat = await uow.chats.get_by_tg_user(uow.session, bot.id, db_user.id)

            is_new_chat = False
            if not chat:
                chat = await uow.chats.create(
                    uow.session,
                    {
                        "bot_id": bot.id,
                        "telegram_user_id": db_user.id,
                        "status": ChatStatus.OPEN,
                    },
                )
                await uow.session.flush()
                is_new_chat = True

            content = typed_msg.text or typed_msg.caption or ""
            msg_type = _CONTENT_TO_MESSAGE_TYPE.get(
                classified.content_type or ContentType.UNKNOWN, MessageType.MEDIA
            )

            msg_data = {
                "chat_id": chat.id,
                "sender_type": SenderType.USER,
                "message_type": msg_type,
                "tg_message_id": typed_msg.message_id,
                "content": content,
                "metadata_info": {
                    "tg_date": typed_msg.date,
                    "content_type": (
                        classified.content_type.value
                        if classified.content_type
                        else None
                    ),
                },
            }

            new_message = await uow.messages.create(uow.session, msg_data)

            await uow.session.flush()
            await uow.commit()

            logger.info(
                "Processed webhook for Bot %s, User %s, Msg %s",
                bot.id,
                db_user.tg_user_id,
                typed_msg.message_id,
            )

        bot_id_str = str(bot.id)
        chat_id_str = str(chat.id)

        if is_new_chat:
            await self._publish_chat_created(bot_id_str, chat_id_str, tg_user_data)

        await self._publish_message_created(
            bot_id_str,
            chat_id_str,
            str(new_message.id),
            typed_msg.message_id,
            content,
            SenderType.USER,
        )

        return SuccessResponse(success=True)
