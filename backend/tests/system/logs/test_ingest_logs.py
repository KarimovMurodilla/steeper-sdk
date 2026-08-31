"""Authentication, truncation, and fan-out behaviour of bot log ingestion.

The ingest endpoint is authenticated only by the
``x-telegram-bot-api-secret-token`` header, exactly like the webhook endpoints,
so these tests pin the 200 / 403 / 404 contract, the two things that keep a
noisy bot from hurting the platform (oversized values are truncated instead of
rejected, batch size is capped), and the shape of what reaches Loki.
"""

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InfrastructureException,
    InstanceNotFoundException,
)
from src.realtime.enums import EventType
from src.system.logs.enums import LogLevel
from src.system.logs.loki import LokiError
from src.system.logs.schemas import BotLogBatchPayload
from src.system.logs.usecases import ingest_logs as ingest_logs_module
from src.system.logs.usecases.ingest_logs import (
    MAX_EXC_CHARS,
    MAX_MESSAGE_CHARS,
    IngestBotLogsUseCase,
)
from tests.communication.fakes import FakeSession, make_bot

TOKEN_HASH = "b" * 64


class FakeLokiClient:
    """Records pushes instead of dialling Loki; can be told to fail."""

    def __init__(self, fail: bool = False) -> None:
        self.pushes: list[tuple[str, list[dict[str, Any]]]] = []
        self.fail = fail

    async def push(self, bot_id: str, records: list[dict[str, Any]]) -> None:
        if self.fail:
            raise LokiError("Loki push rejected with 429: rate limited")
        self.pushes.append((bot_id, records))


class FakeLogsUnitOfWork:
    """Async-context-manager stand-in for ApplicationUnitOfWork."""

    def __init__(self, bot: Any = None) -> None:
        self.session = FakeSession()
        self.bots = SimpleNamespace(get_single=self._get_bot)
        self._bot = bot

    async def _get_bot(self, session: Any, **kwargs: Any) -> Any:
        return self._bot

    async def __aenter__(self) -> "FakeLogsUnitOfWork":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None


@pytest.fixture(autouse=True)
def silence_broker(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Capture real-time publishes instead of dialling RabbitMQ."""
    published: list[dict[str, Any]] = []

    async def fake_publish(payload: Any, **kwargs: Any) -> None:
        published.append({"payload": payload, **kwargs})

    monkeypatch.setattr(ingest_logs_module.broker, "publish", fake_publish)
    return published


def _batch(count: int = 1, **overrides: Any) -> BotLogBatchPayload:
    record: dict[str, Any] = {
        "ts": 1700000000.123,
        "level": LogLevel.ERROR,
        "logger": "app.handlers.start",
        "message": "Boom",
        "module": "handlers",
        "func": "cmd_start",
        "line": 42,
        "exc": None,
        "extra": {"chat_id": 1},
    }
    record.update(overrides)
    return BotLogBatchPayload.model_validate({"records": [record] * count})


async def test_ingest_unknown_bot_raises_not_found() -> None:
    loki = FakeLokiClient()
    use_case = IngestBotLogsUseCase(FakeLogsUnitOfWork(bot=None), loki)

    with pytest.raises(InstanceNotFoundException) as exc_info:
        await use_case.execute(uuid4(), _batch(), TOKEN_HASH)

    assert exc_info.value.code == ErrorCode.BOT_NOT_FOUND
    assert loki.pushes == []


@pytest.mark.parametrize(
    "provided_token",
    ["", "c" * 64, TOKEN_HASH[:-1]],
    ids=["missing-header", "wrong-hash", "truncated-hash"],
)
async def test_ingest_invalid_secret_raises_forbidden(provided_token: str) -> None:
    loki = FakeLokiClient()
    uow = FakeLogsUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))

    with pytest.raises(AccessForbiddenException) as exc_info:
        await IngestBotLogsUseCase(uow, loki).execute(uuid4(), _batch(), provided_token)

    assert exc_info.value.code == ErrorCode.AUTH_ACCESS_FORBIDDEN
    assert loki.pushes == []


async def test_ingest_pushes_batch_and_publishes_one_event(
    silence_broker: list[dict[str, Any]],
) -> None:
    loki = FakeLokiClient()
    uow = FakeLogsUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))
    bot_id = uuid4()

    response = await IngestBotLogsUseCase(uow, loki).execute(
        bot_id, _batch(count=3), TOKEN_HASH
    )

    assert response.success is True
    # One push per batch, not per record.
    assert len(loki.pushes) == 1
    pushed_bot_id, pushed = loki.pushes[0]
    assert pushed_bot_id == str(bot_id)
    assert len(pushed) == 3
    assert pushed[0]["logger"] == "app.handlers.start"
    assert pushed[0]["func"] == "cmd_start"

    # One frame for the whole batch: per-record frames would flood the socket.
    assert len(silence_broker) == 1
    envelope = silence_broker[0]["payload"]
    assert envelope["event"] == EventType.BOT_LOG_CREATED
    assert envelope["chat_id"] is None
    assert len(envelope["data"]["records"]) == 3
    assert silence_broker[0]["routing_key"].endswith(".log.created")


async def test_ingest_storage_failure_raises_infrastructure_error(
    silence_broker: list[dict[str, Any]],
) -> None:
    """A rejected push must surface, not be swallowed behind a 200."""
    loki = FakeLokiClient(fail=True)
    uow = FakeLogsUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))

    with pytest.raises(InfrastructureException) as exc_info:
        await IngestBotLogsUseCase(uow, loki).execute(uuid4(), _batch(), TOKEN_HASH)

    assert exc_info.value.code == ErrorCode.BOT_LOGS_STORAGE_UNAVAILABLE
    assert silence_broker == []


async def test_ingest_stores_logs_of_a_disabled_bot() -> None:
    """Logs are operational data — they stay useful while a bot is switched off."""
    loki = FakeLokiClient()
    uow = FakeLogsUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH, status="disabled"))

    response = await IngestBotLogsUseCase(uow, loki).execute(
        uuid4(), _batch(), TOKEN_HASH
    )

    assert response.success is True
    assert len(loki.pushes[0][1]) == 1


async def test_ingest_truncates_oversized_values() -> None:
    loki = FakeLokiClient()
    uow = FakeLogsUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))
    payload = _batch(
        message="x" * (MAX_MESSAGE_CHARS + 100),
        exc="y" * (MAX_EXC_CHARS + 100),
    )

    await IngestBotLogsUseCase(uow, loki).execute(uuid4(), payload, TOKEN_HASH)

    pushed = loki.pushes[0][1][0]
    assert pushed["message"].startswith("x" * MAX_MESSAGE_CHARS)
    assert pushed["message"].endswith("[truncated]")
    assert pushed["exc"].startswith("y" * MAX_EXC_CHARS)
    assert pushed["exc"].endswith("[truncated]")


def test_batch_size_is_capped() -> None:
    """A single request must not be able to push an unbounded number of records."""
    with pytest.raises(ValueError):
        BotLogBatchPayload.model_validate({"records": []})

    record = _batch().records[0].model_dump(mode="json")
    with pytest.raises(ValueError):
        BotLogBatchPayload.model_validate({"records": [record] * 501})
