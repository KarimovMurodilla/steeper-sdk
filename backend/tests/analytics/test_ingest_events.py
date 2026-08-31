"""Ingestion of product events reported by a bot."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.analytics.schemas import BotEventBatchPayload
from src.analytics.usecases.ingest_events import IngestBotEventsUseCase
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
)
from tests.analytics.fakes import FakeUnitOfWork, make_bot

SECRET = "b" * 64
NOW = datetime.now(UTC)


def batch(**overrides: object) -> BotEventBatchPayload:
    event: dict[str, object] = {
        "name": "checkout_started",
        "tg_user_id": 123456789,
        "ts": NOW,
        "props": {"plan": "pro"},
    }
    event.update(overrides)
    return BotEventBatchPayload(events=[event])  # type: ignore[list-item]


async def test_events_are_stored_with_the_resolved_user() -> None:
    bot = make_bot(token_hash=SECRET)
    user_id = uuid4()
    uow = FakeUnitOfWork(bot=bot, known_users={123456789: user_id})
    use_case = IngestBotEventsUseCase(uow=uow)  # type: ignore[arg-type]

    result = await use_case.execute(bot.id, batch(), SECRET)

    assert result.success is True
    assert uow.commits == 1
    stored = uow.bot_events.inserted
    assert len(stored) == 1
    assert stored[0]["name"] == "checkout_started"
    assert stored[0]["tg_user_id"] == 123456789
    assert stored[0]["telegram_user_id"] == user_id
    assert stored[0]["props"] == {"plan": "pro"}


async def test_an_unknown_user_is_still_recorded() -> None:
    # An event may legitimately arrive before the user has ever messaged the
    # bot; the funnel matches on the raw Telegram id anyway.
    bot = make_bot(token_hash=SECRET)
    uow = FakeUnitOfWork(bot=bot, known_users={})
    use_case = IngestBotEventsUseCase(uow=uow)  # type: ignore[arg-type]

    await use_case.execute(bot.id, batch(), SECRET)

    assert uow.bot_events.inserted[0]["telegram_user_id"] is None


async def test_unknown_bot_is_rejected() -> None:
    uow = FakeUnitOfWork(bot=None)
    use_case = IngestBotEventsUseCase(uow=uow)  # type: ignore[arg-type]

    with pytest.raises(InstanceNotFoundException):
        await use_case.execute(uuid4(), batch(), SECRET)

    assert uow.bot_events.inserted == []


async def test_invalid_secret_is_rejected() -> None:
    bot = make_bot(token_hash=SECRET)
    uow = FakeUnitOfWork(bot=bot)
    use_case = IngestBotEventsUseCase(uow=uow)  # type: ignore[arg-type]

    with pytest.raises(AccessForbiddenException):
        await use_case.execute(bot.id, batch(), "wrong")

    assert uow.bot_events.inserted == []


async def test_events_from_a_badly_skewed_clock_are_dropped() -> None:
    # A bot clock hours ahead would order that user's steps in front of events
    # we timestamped correctly, so the funnel for them would read wrong.
    bot = make_bot(token_hash=SECRET)
    uow = FakeUnitOfWork(bot=bot)
    use_case = IngestBotEventsUseCase(uow=uow)  # type: ignore[arg-type]

    result = await use_case.execute(bot.id, batch(ts=NOW + timedelta(hours=3)), SECRET)

    assert result.success is True
    assert uow.bot_events.inserted == []


async def test_a_small_clock_skew_is_tolerated() -> None:
    bot = make_bot(token_hash=SECRET)
    uow = FakeUnitOfWork(bot=bot)
    use_case = IngestBotEventsUseCase(uow=uow)  # type: ignore[arg-type]

    await use_case.execute(bot.id, batch(ts=NOW + timedelta(minutes=5)), SECRET)

    assert len(uow.bot_events.inserted) == 1


def test_batch_size_is_capped() -> None:
    from pydantic import ValidationError

    events = [
        {"name": "a", "tg_user_id": 1, "ts": NOW, "props": {}} for _ in range(501)
    ]
    with pytest.raises(ValidationError):
        BotEventBatchPayload(events=events)  # type: ignore[arg-type]


def test_an_empty_batch_is_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BotEventBatchPayload(events=[])


def test_an_empty_event_name_is_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        batch(name="")
