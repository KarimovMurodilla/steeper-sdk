"""Use case: cursor-paginated log history for a bot."""

from datetime import datetime
from uuid import UUID

from loggers import get_logger
from src.communication.schemas import CursorPaginatedResponse
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import InfrastructureException
from src.system.logs.enums import LogLevel
from src.system.logs.loki import LokiClient, LokiError, from_unix_ns
from src.system.logs.schemas import BotLogViewModel

logger = get_logger(__name__)


class ListBotLogsUseCase:
    """Returns cursor-paginated log records for a bot (newest first).

    The cursor is a Unix-nanosecond timestamp rather than a row ID: Loki paginates
    by time. Its ``end`` bound is exclusive, so handing back the last item's
    timestamp yields the next page — at the cost of dropping any other record
    sharing that exact nanosecond, which is why the panel de-duplicates on
    (cursor, message) instead of relying on the page boundary alone.
    """

    def __init__(self, loki: LokiClient) -> None:
        self.loki = loki

    async def execute(
        self,
        bot_id: UUID,
        limit: int = 100,
        cursor: str | None = None,
        levels: list[LogLevel] | None = None,
        logger_name: str | None = None,
        search: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> CursorPaginatedResponse[BotLogViewModel]:
        """
        Executes the business logic for listing a bot's log records.

        Args:
            bot_id (UUID): The unique identifier of the bot.
            limit (int, optional): Maximum records to fetch. Defaults to 100.
            cursor (str | None, optional): Unix-nanosecond timestamp of the last
                item of the previous page. Defaults to None.
            levels (list[LogLevel] | None, optional): Keep only these levels.
            logger_name (str | None, optional): Keep loggers with this prefix.
            search (str | None, optional): Case-sensitive substring of the line.
            since (datetime | None, optional): Lower bound on the record timestamp.
            until (datetime | None, optional): Exclusive upper bound on the timestamp.

        Returns:
            CursorPaginatedResponse[BotLogViewModel]: The cursor-paginated items.

        Raises:
            InfrastructureException: If Loki is unreachable or rejects the query.
        """
        end = until
        if cursor is not None:
            cursor_ts = from_unix_ns(int(cursor))
            # An explicit `until` still wins if it is the tighter bound.
            end = min(cursor_ts, until) if until is not None else cursor_ts

        try:
            entries = await self.loki.query_range(
                bot_id=str(bot_id),
                limit=limit,
                levels=levels,
                logger_name=logger_name,
                search=search,
                since=since,
                until=end,
            )
        except LokiError as e:
            logger.error("Failed to read logs of bot %s: %s", bot_id, e)
            raise InfrastructureException(ErrorCode.BOT_LOGS_STORAGE_UNAVAILABLE) from e

        items = [
            BotLogViewModel(
                cursor=str(ts_ns),
                ts=from_unix_ns(ts_ns),
                level=LogLevel(level),
                logger=line.get("logger") or "",
                message=line.get("message") or "",
                module=line.get("module"),
                func=line.get("func"),
                line=line.get("line"),
                exc=line.get("exc"),
                extra=line.get("extra") or {},
            )
            for ts_ns, level, line in entries
        ]

        next_cursor = items[-1].cursor if len(items) == limit else None

        return CursorPaginatedResponse[BotLogViewModel](
            items=items,
            next_cursor=next_cursor,
        )
