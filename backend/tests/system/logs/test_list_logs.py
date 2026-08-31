"""Pagination semantics of the log history use case.

Loki paginates by time, not by row ID, so the cursor is a nanosecond timestamp
and Loki's exclusive ``end`` bound is what makes it work. These tests pin that
translation and the mapping of a stored line back into the panel's view model.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import InfrastructureException
from src.system.logs.enums import LogLevel
from src.system.logs.loki import LokiError, to_unix_ns
from src.system.logs.usecases.list_logs import ListBotLogsUseCase


class FakeLokiClient:
    def __init__(
        self,
        entries: list[tuple[int, str, dict[str, Any]]] | None = None,
        fail: bool = False,
    ) -> None:
        self.entries = entries or []
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    async def query_range(self, **kwargs: Any) -> list[tuple[int, str, dict[str, Any]]]:
        if self.fail:
            raise LokiError("connection refused")
        self.calls.append(kwargs)
        return self.entries


def _entry(ts_ns: int, message: str = "Boom") -> tuple[int, str, dict[str, Any]]:
    return (
        ts_ns,
        "ERROR",
        {
            "message": message,
            "logger": "app.handlers",
            "module": "handlers",
            "func": "cmd_start",
            "line": 42,
            "exc": None,
            "extra": {"chat_id": 1},
        },
    )


async def test_maps_stored_line_into_view_model() -> None:
    moment = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    loki = FakeLokiClient([_entry(to_unix_ns(moment))])

    page = await ListBotLogsUseCase(loki).execute(uuid4(), limit=10)

    item = page.items[0]
    assert item.ts == moment
    assert item.cursor == str(to_unix_ns(moment))
    assert item.level == LogLevel.ERROR
    assert item.logger == "app.handlers"
    assert item.extra == {"chat_id": 1}
    # A short page means there is nothing more to fetch.
    assert page.next_cursor is None


async def test_full_page_returns_last_timestamp_as_cursor() -> None:
    loki = FakeLokiClient([_entry(300), _entry(200)])

    page = await ListBotLogsUseCase(loki).execute(uuid4(), limit=2)

    assert page.next_cursor == "200"


async def test_cursor_becomes_the_exclusive_upper_bound() -> None:
    loki = FakeLokiClient()

    await ListBotLogsUseCase(loki).execute(
        uuid4(), limit=10, cursor="1700000000000000000"
    )

    assert loki.calls[0]["until"] == datetime(2023, 11, 14, 22, 13, 20, tzinfo=UTC)


async def test_explicit_until_wins_when_tighter_than_cursor() -> None:
    loki = FakeLokiClient()
    until = datetime(2020, 1, 1, tzinfo=UTC)

    await ListBotLogsUseCase(loki).execute(
        uuid4(), limit=10, cursor="1700000000000000000", until=until
    )

    assert loki.calls[0]["until"] == until


async def test_storage_failure_raises_infrastructure_error() -> None:
    loki = FakeLokiClient(fail=True)

    with pytest.raises(InfrastructureException) as exc_info:
        await ListBotLogsUseCase(loki).execute(uuid4(), limit=10)

    assert exc_info.value.code == ErrorCode.BOT_LOGS_STORAGE_UNAVAILABLE
