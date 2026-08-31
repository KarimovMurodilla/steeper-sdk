"""Use case: store a batch of product events reported by a bot."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from loggers import get_logger
from src.analytics.constants import MAX_EVENT_CLOCK_SKEW
from src.analytics.schemas import BotEventBatchPayload
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
)
from src.core.schemas import SuccessResponse
from src.core.utils.security import verify_secret_token

logger = get_logger(__name__)


class IngestBotEventsUseCase:
    """
    Accepts product events from a bot process and appends them to ``bot_events``.

    Authentication matches the webhook and log endpoints: the bot is named by
    ``bot_id`` in the path and proves itself with the SHA-256 of its Telegram
    token in the secret header.
    """

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(
        self,
        bot_id: UUID,
        payload: BotEventBatchPayload,
        secret_token: str,
    ) -> SuccessResponse:
        """
        Executes the business logic for ingesting a batch of product events.

        Args:
            bot_id (UUID): The unique identifier of the bot that emitted them.
            payload (BotEventBatchPayload): The batch of events.
            secret_token (str): The security token to validate the request.

        Returns:
            SuccessResponse: A success confirmation response.

        Raises:
            InstanceNotFoundException: If the bot is not found.
            AccessForbiddenException: If the secret token is invalid.
        """
        async with self.uow as uow:
            bot = await uow.bots.get_single(uow.session, id=bot_id)

            if not bot:
                logger.warning("Event batch received for unknown bot_id: %s", bot_id)
                raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            if not verify_secret_token(bot.token_hash, secret_token):
                logger.warning(
                    "Event batch received with invalid secret token for bot: %s", bot_id
                )
                raise AccessForbiddenException(ErrorCode.AUTH_ACCESS_FORBIDDEN)

            horizon = datetime.now(UTC) + MAX_EVENT_CLOCK_SKEW
            accepted = [event for event in payload.events if event.ts <= horizon]
            skipped = len(payload.events) - len(accepted)
            if skipped:
                # A bot clock far ahead of ours would order that user's steps
                # in front of events we timestamped correctly, so the whole
                # funnel for them would read wrong. Drop rather than distort.
                logger.warning(
                    "Dropped %d of %d events from bot %s: timestamp too far ahead",
                    skipped,
                    len(payload.events),
                    bot_id,
                )
            if not accepted:
                return SuccessResponse(success=True)

            # Best-effort: an event may legitimately arrive for a user who has
            # never sent the bot a message, and the funnel matches on the raw
            # Telegram id anyway.
            known_users = await uow.telegram_users.resolve_ids(
                uow.session, bot_id, [event.tg_user_id for event in accepted]
            )

            values: list[dict[str, Any]] = [
                {
                    "bot_id": bot_id,
                    "telegram_user_id": known_users.get(event.tg_user_id),
                    "tg_user_id": event.tg_user_id,
                    "name": event.name,
                    "props": event.props,
                    "ts": event.ts,
                }
                for event in accepted
            ]
            await uow.bot_events.bulk_insert(uow.session, values)
            await uow.commit()

        logger.debug("Stored %d events for bot %s", len(values), bot_id)
        return SuccessResponse(success=True)
