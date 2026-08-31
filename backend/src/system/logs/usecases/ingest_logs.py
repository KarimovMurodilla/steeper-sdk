import time
from typing import Any
from uuid import UUID

from loggers import get_logger
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InfrastructureException,
    InstanceNotFoundException,
)
from src.core.schemas import SuccessResponse
from src.core.utils.security import verify_secret_token
from src.realtime.broker import broker, steeper_exchange
from src.realtime.enums import EventType
from src.realtime.schemas import WSDownlinkEnvelope
from src.system.logs.loki import LokiClient, LokiError, to_unix_ns
from src.system.logs.schemas import (
    BotLogBatchPayload,
    BotLogViewModel,
    WSBotLogCreatedData,
)

logger = get_logger(__name__)

# A runaway log line must not be able to bloat a chunk unboundedly. Long values
# are truncated rather than rejected — dropping the whole batch would lose the
# surrounding context, which is exactly what the operator came for.
MAX_MESSAGE_CHARS = 20_000
MAX_EXC_CHARS = 50_000
_TRUNCATION_MARKER = "… [truncated]"


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + _TRUNCATION_MARKER


class IngestBotLogsUseCase:
    """Stores a batch of log records shipped by a bot and fans it out live.

    The client library sends batches fire-and-forget, so this path is the hot
    one of the whole logging feature: it authenticates the bot, pushes the batch
    to Loki in a single request, and publishes one realtime event for the whole
    batch.
    """

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
        loki: LokiClient,
    ) -> None:
        self.uow = uow
        self.loki = loki

    async def _publish_logs_created(
        self, bot_id_str: str, items: list[BotLogViewModel]
    ) -> None:
        """Publishes the ingested batch as a single realtime event."""
        routing_key = f"bot.{bot_id_str}.log.created"
        envelope = WSDownlinkEnvelope(
            version=1,
            event=EventType.BOT_LOG_CREATED,
            bot_id=bot_id_str,
            chat_id=None,
            timestamp=int(time.time()),
            data=WSBotLogCreatedData(records=items).model_dump(mode="json"),
        )
        try:
            await broker.publish(
                envelope.model_dump(mode="json"),
                routing_key=routing_key,
                exchange=steeper_exchange,
            )
            logger.debug(
                "Published %s event (%d records) to %s",
                EventType.BOT_LOG_CREATED,
                len(items),
                routing_key,
            )
        except Exception as e:
            logger.exception(
                "Failed to publish BOT_LOG_CREATED event to RabbitMQ: %s", e
            )

    async def execute(
        self,
        bot_id: UUID,
        payload: BotLogBatchPayload,
        secret_token: str,
    ) -> SuccessResponse:
        """
        Executes the business logic for ingesting a batch of bot log records.

        Args:
            bot_id (UUID): The unique identifier of the bot that emitted the logs.
            payload (BotLogBatchPayload): The batch of log records.
            secret_token (str): The security token to validate the request.

        Returns:
            SuccessResponse: A success confirmation response.

        Raises:
            InstanceNotFoundException: If the bot is not found.
            AccessForbiddenException: If the secret token is invalid.
            InfrastructureException: If Loki rejected or could not take the batch.
        """
        async with self.uow as uow:
            bot = await uow.bots.get_single(uow.session, id=bot_id)

            if not bot:
                logger.warning("Log batch received for unknown bot_id: %s", bot_id)
                raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            if not verify_secret_token(bot.token_hash, secret_token):
                logger.warning(
                    "Log batch received with invalid secret token for bot: %s", bot_id
                )
                raise AccessForbiddenException(ErrorCode.AUTH_ACCESS_FORBIDDEN)

        bot_id_str = str(bot_id)
        records: list[dict[str, Any]] = [
            {
                "ts": record.ts,
                "level": record.level,
                "logger": record.logger,
                "message": _truncate(record.message, MAX_MESSAGE_CHARS),
                "module": record.module,
                "func": record.func,
                "line": record.line,
                "exc": (
                    _truncate(record.exc, MAX_EXC_CHARS)
                    if record.exc is not None
                    else None
                ),
                "extra": record.extra,
            }
            for record in payload.records
        ]

        try:
            await self.loki.push(bot_id_str, records)
        except LokiError as e:
            logger.error("Failed to store %d log records: %s", len(records), e)
            raise InfrastructureException(ErrorCode.BOT_LOGS_STORAGE_UNAVAILABLE) from e

        items = [
            BotLogViewModel(
                cursor=str(to_unix_ns(record["ts"])),
                ts=record["ts"],
                level=record["level"],
                logger=record["logger"],
                message=record["message"],
                module=record["module"],
                func=record["func"],
                line=record["line"],
                exc=record["exc"],
                extra=record["extra"],
            )
            for record in records
        ]

        logger.debug("Stored %d log records for bot %s", len(items), bot_id)

        await self._publish_logs_created(bot_id_str, items)

        return SuccessResponse(success=True)
