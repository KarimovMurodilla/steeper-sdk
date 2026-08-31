"""Loki client for bot logs — the storage layer of the logging feature.

Logs live in Loki rather than PostgreSQL: the volume is unbounded and
write-heavy, retention is a storage concern (Loki's compactor owns it), and the
only reads are "tail this bot's logs" and "grep this bot's logs" — exactly what
a log store is built for.

Label discipline is the one thing that matters here. Loki creates a stream per
unique label combination, so only low-cardinality dimensions are labels
(``app``, ``bot_id``, ``level``). Everything else — logger name, module,
function, line, traceback, structured extras — is encoded in the JSON log line
and filtered with LogQL's ``| json`` stage.
"""

from datetime import UTC, datetime, timedelta
import json
import re
from typing import Any

import httpx

from loggers import get_logger
from src.core.utils.datetime_utils import get_utc_now
from src.system.logs.enums import LogLevel

logger = get_logger(__name__)

# Label attached to every stream, so a query can never accidentally span
# whatever else may be pushed into the same Loki instance later.
APP_LABEL = "steeper-bot"

# Reads default to the retention window; without a lower bound Loki would have
# to be given one anyway, and a wider one only scans chunks that are gone.
DEFAULT_LOOKBACK = timedelta(days=14)

_NS_PER_SECOND = 1_000_000_000


class LokiError(Exception):
    """Raised when Loki is unreachable or rejects a request."""


def to_unix_ns(value: datetime) -> int:
    """Convert a datetime to the Unix-nanosecond timestamps Loki speaks."""
    return int(value.timestamp() * _NS_PER_SECOND)


def from_unix_ns(value: int) -> datetime:
    """Convert Loki's Unix-nanosecond timestamp back to an aware datetime."""
    return datetime.fromtimestamp(value / _NS_PER_SECOND, tz=UTC)


def _quote(value: str) -> str:
    """Quote a LogQL string literal (Go-style escaping, same as JSON)."""
    return json.dumps(value)


class LokiClient:
    """Thin async wrapper over the two Loki endpoints this feature needs.

    One ``httpx.AsyncClient`` is kept for the process lifetime — ingestion is
    the hot path, and a fresh connection per batch would dominate its cost.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        max_limit: int = 500,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_limit = max_limit
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    async def aclose(self) -> None:
        """Close the underlying HTTP client (called on application shutdown)."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    # ----- Write path ----- #

    async def push(self, bot_id: str, records: list[dict[str, Any]]) -> None:
        """Push a batch of log records, grouped into one stream per level.

        Args:
            bot_id: The bot the records belong to; becomes a stream label.
            records: Normalized records, each with ``ts`` (datetime), ``level``
                and the JSON-serializable payload fields.

        Raises:
            LokiError: If Loki is unreachable or rejects the batch.
        """
        by_level: dict[str, list[list[str]]] = {}
        for record in records:
            ts: datetime = record["ts"]
            level = str(record["level"])
            line = {
                "message": record["message"],
                "logger": record["logger"],
                "module": record["module"],
                "func": record["func"],
                "line": record["line"],
                "exc": record["exc"],
                "extra": record["extra"],
            }
            by_level.setdefault(level, []).append(
                [str(to_unix_ns(ts)), json.dumps(line, ensure_ascii=False)]
            )

        payload = {
            "streams": [
                {
                    "stream": {"app": APP_LABEL, "bot_id": bot_id, "level": level},
                    "values": values,
                }
                for level, values in by_level.items()
            ]
        }

        try:
            response = await self._get_client().post(
                "/loki/api/v1/push",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        except httpx.HTTPError as e:
            raise LokiError(f"Loki push failed: {e}") from e

        if response.status_code >= 400:
            # Loki answers 400 for out-of-window timestamps (a bot with a skewed
            # clock) and 429 when a bot floods; both are worth the exact text.
            raise LokiError(
                f"Loki push rejected with {response.status_code}: {response.text[:500]}"
            )

    # ----- Read path ----- #

    def build_query(
        self,
        bot_id: str,
        levels: list[LogLevel] | None = None,
        logger_name: str | None = None,
        search: str | None = None,
    ) -> str:
        """Build the LogQL query for a bot's log stream."""
        selector = [f"app={_quote(APP_LABEL)}", f"bot_id={_quote(bot_id)}"]
        if levels:
            if len(levels) == 1:
                selector.append(f"level={_quote(str(levels[0]))}")
            else:
                pattern = "|".join(str(level) for level in levels)
                selector.append(f"level=~{_quote(pattern)}")

        query = "{" + ", ".join(selector) + "}"

        # A line filter runs before JSON parsing, so it is the cheap one; keep it
        # first when the operator searched for text.
        if search:
            query += f" |= {_quote(search)}"
        if logger_name:
            query += f" | json | logger=~{_quote('^' + re.escape(logger_name) + '.*')}"

        return query

    async def query_range(
        self,
        bot_id: str,
        limit: int,
        levels: list[LogLevel] | None = None,
        logger_name: str | None = None,
        search: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[tuple[int, str, dict[str, Any]]]:
        """Fetch log entries newest-first.

        ``until`` doubles as the pagination cursor: Loki's ``end`` is exclusive,
        so passing the timestamp of the last entry of a page yields the next one.

        Returns:
            A list of ``(unix_ns, level, parsed_line)`` tuples, newest first.

        Raises:
            LokiError: If Loki is unreachable or rejects the query.
        """
        end = until or get_utc_now()
        start = since or (end - DEFAULT_LOOKBACK)

        params = {
            "query": self.build_query(bot_id, levels, logger_name, search),
            "start": str(to_unix_ns(start)),
            "end": str(to_unix_ns(end)),
            "limit": str(min(limit, self.max_limit)),
            "direction": "backward",
        }

        try:
            response = await self._get_client().get(
                "/loki/api/v1/query_range", params=params
            )
        except httpx.HTTPError as e:
            raise LokiError(f"Loki query failed: {e}") from e

        if response.status_code >= 400:
            raise LokiError(
                f"Loki query rejected with {response.status_code}: {response.text[:500]}"
            )

        body = response.json()
        entries: list[tuple[int, str, dict[str, Any]]] = []

        for stream in body.get("data", {}).get("result", []):
            level = stream.get("stream", {}).get("level", LogLevel.INFO.value)
            for raw_ts, raw_line in stream.get("values", []):
                try:
                    parsed = json.loads(raw_line)
                except json.JSONDecodeError:
                    # A line that is not our JSON is still worth showing.
                    parsed = {"message": raw_line}
                entries.append((int(raw_ts), level, parsed))

        # Loki sorts within a stream, not across them; one stream per level means
        # a merge is always needed before the page is cut.
        entries.sort(key=lambda entry: entry[0], reverse=True)
        return entries[:limit]
