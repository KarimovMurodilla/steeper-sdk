"""LogQL construction, push shaping, and pagination semantics of LokiClient.

These are the parts that cannot be checked against a real Loki in CI but decide
whether the feature stays cheap: label cardinality (only app / bot_id / level
are labels), correct escaping of operator-supplied filter text, and the
cross-stream merge that makes time-ordered pagination correct.
"""

from datetime import UTC, datetime
import json
from typing import Any

import httpx
import pytest

from src.system.logs.enums import LogLevel
from src.system.logs.loki import (
    APP_LABEL,
    LokiClient,
    LokiError,
    from_unix_ns,
    to_unix_ns,
)


def _client(handler: Any) -> LokiClient:
    client = LokiClient(base_url="http://loki:3100")
    client._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="http://loki:3100",
        transport=httpx.MockTransport(handler),
    )
    return client


def _record(level: LogLevel = LogLevel.ERROR, **overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "ts": datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        "level": level,
        "logger": "app.handlers",
        "message": "Boom",
        "module": "handlers",
        "func": "cmd_start",
        "line": 42,
        "exc": None,
        "extra": {},
    }
    record.update(overrides)
    return record


# ----- Query construction ----- #


def test_query_uses_only_low_cardinality_labels() -> None:
    query = LokiClient("http://loki:3100").build_query("bot-1")

    assert query == f'{{app="{APP_LABEL}", bot_id="bot-1"}}'


def test_single_level_uses_equality_and_many_use_regex() -> None:
    client = LokiClient("http://loki:3100")

    assert 'level="ERROR"' in client.build_query("bot-1", levels=[LogLevel.ERROR])
    assert 'level=~"ERROR|CRITICAL"' in client.build_query(
        "bot-1", levels=[LogLevel.ERROR, LogLevel.CRITICAL]
    )


def test_logger_prefix_is_anchored_and_escaped() -> None:
    query = LokiClient("http://loki:3100").build_query(
        "bot-1", logger_name="app.handlers"
    )

    assert "| json | logger=~" in query
    # The dot must not stay a regex wildcard.
    assert "app\\\\.handlers" in query


def test_search_text_is_quoted_safely() -> None:
    """Operator input must not be able to break out of the LogQL literal."""
    query = LokiClient("http://loki:3100").build_query("bot-1", search='"} | drop me')

    assert query.endswith('|= "\\"} | drop me"')


# ----- Push ----- #


async def test_push_groups_records_into_one_stream_per_level() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        captured["url"] = str(request.url)
        return httpx.Response(204)

    await _client(handler).push(
        "bot-1",
        [_record(LogLevel.ERROR), _record(LogLevel.INFO), _record(LogLevel.ERROR)],
    )

    assert captured["url"].endswith("/loki/api/v1/push")
    streams = captured["body"]["streams"]
    assert len(streams) == 2
    by_level = {stream["stream"]["level"]: stream for stream in streams}
    assert set(by_level["ERROR"]["stream"]) == {"app", "bot_id", "level"}
    assert len(by_level["ERROR"]["values"]) == 2
    assert len(by_level["INFO"]["values"]) == 1

    ts, line = by_level["INFO"]["values"][0]
    assert ts == str(to_unix_ns(datetime(2026, 1, 1, 12, 0, tzinfo=UTC)))
    # Everything high-cardinality travels inside the line, not in labels.
    assert json.loads(line)["logger"] == "app.handlers"


async def test_push_raises_on_rejection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="entry too far behind")

    with pytest.raises(LokiError) as exc_info:
        await _client(handler).push("bot-1", [_record()])

    assert "400" in str(exc_info.value)


# ----- Query range ----- #


async def test_query_range_merges_streams_and_cuts_to_limit() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "result": [
                        {
                            "stream": {"level": "ERROR"},
                            "values": [
                                ["300", json.dumps({"message": "c"})],
                                ["100", json.dumps({"message": "a"})],
                            ],
                        },
                        {
                            "stream": {"level": "INFO"},
                            "values": [["200", json.dumps({"message": "b"})]],
                        },
                    ]
                }
            },
        )

    entries = await _client(handler).query_range("bot-1", limit=2)

    # Loki sorts within a stream only; the merge must interleave by timestamp.
    assert [ts for ts, _, _ in entries] == [300, 200]
    assert [level for _, level, _ in entries] == ["ERROR", "INFO"]


async def test_query_range_sends_backward_direction_and_bounds() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": {"result": []}})

    since = datetime(2026, 1, 1, tzinfo=UTC)
    until = datetime(2026, 1, 2, tzinfo=UTC)
    await _client(handler).query_range("bot-1", limit=10, since=since, until=until)

    assert captured["params"]["direction"] == "backward"
    assert captured["params"]["start"] == str(to_unix_ns(since))
    assert captured["params"]["end"] == str(to_unix_ns(until))
    assert captured["params"]["limit"] == "10"


async def test_query_range_limit_is_capped_by_config() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": {"result": []}})

    client = _client(handler)
    client.max_limit = 50
    await client.query_range("bot-1", limit=5000)

    assert captured["params"]["limit"] == "50"


async def test_query_range_keeps_unparsable_lines() -> None:
    """A line that is not our JSON is still worth showing to the operator."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": {
                    "result": [
                        {"stream": {"level": "INFO"}, "values": [["100", "raw text"]]}
                    ]
                }
            },
        )

    entries = await _client(handler).query_range("bot-1", limit=10)

    assert entries[0][2] == {"message": "raw text"}


def test_timestamp_round_trip() -> None:
    moment = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    assert from_unix_ns(to_unix_ns(moment)) == moment
