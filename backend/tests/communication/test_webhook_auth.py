"""Authentication and short-circuit behaviour of the webhook use cases.

Both public webhook endpoints are authenticated only by the
``x-telegram-bot-api-secret-token`` header, so these tests pin the 200 / 403 /
404 contract, the constant-time comparison rejecting a missing header, and the
branches that must never reach the message workflow (unknown bot, disabled bot,
duplicate update).
"""

from typing import Any
from uuid import uuid4

import pytest

from src.communication.schemas import BotMessagePayload, TelegramUpdatePayload
from src.communication.usecases import (
    handle_webhook as handle_webhook_module,
    log_bot_message as log_bot_message_module,
)
from src.communication.usecases.handle_webhook import HandleWebhookUseCase
from src.communication.usecases.log_bot_message import LogBotMessageUseCase
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
)
from tests.communication.fakes import (
    FakeUnitOfWork,
    make_bot,
    make_chat,
    make_telegram_user,
)

TOKEN_HASH = "b" * 64


@pytest.fixture(autouse=True)
def silence_broker(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Capture real-time publishes instead of dialling RabbitMQ."""
    published: list[dict[str, Any]] = []

    async def fake_publish(payload: Any, **kwargs: Any) -> None:
        published.append({"payload": payload, **kwargs})

    monkeypatch.setattr(handle_webhook_module.broker, "publish", fake_publish)
    monkeypatch.setattr(log_bot_message_module.broker, "publish", fake_publish)
    return published


def _update_payload(update_id: int = 1) -> tuple[TelegramUpdatePayload, dict[str, Any]]:
    raw: dict[str, Any] = {
        "update_id": update_id,
        "message": {
            "message_id": 42,
            "date": 1610000000,
            "text": "hello",
            "chat": {"id": 123456789, "type": "private"},
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "John",
            },
        },
    }
    return TelegramUpdatePayload.model_validate(raw), raw


def _bot_message_payload() -> BotMessagePayload:
    return BotMessagePayload(
        chat_id=123456789, text="Bot reply", message_id=42, date=1610000000
    )


# ----- POST /webhook/{bot_id} ----- #


async def test_webhook_unknown_bot_raises_not_found() -> None:
    uow = FakeUnitOfWork(bot=None)
    payload, raw = _update_payload()

    with pytest.raises(InstanceNotFoundException) as exc_info:
        await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, TOKEN_HASH)

    assert exc_info.value.code == ErrorCode.BOT_NOT_FOUND
    assert uow.telegram_updates.recorded == []
    assert uow.commits == 0


@pytest.mark.parametrize(
    "provided_token",
    ["", "c" * 64, TOKEN_HASH[:-1]],
    ids=["missing-header", "wrong-hash", "truncated-hash"],
)
async def test_webhook_invalid_secret_raises_forbidden(provided_token: str) -> None:
    uow = FakeUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))
    payload, raw = _update_payload()

    with pytest.raises(AccessForbiddenException) as exc_info:
        await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, provided_token)

    assert exc_info.value.code == ErrorCode.AUTH_ACCESS_FORBIDDEN
    assert uow.telegram_updates.recorded == []
    assert uow.messages.created == []
    assert uow.commits == 0


async def test_webhook_blank_stored_hash_never_authenticates() -> None:
    """A bot row with an empty token_hash must not be reachable with no header."""
    uow = FakeUnitOfWork(bot=make_bot(token_hash=""))
    payload, raw = _update_payload()

    with pytest.raises(AccessForbiddenException):
        await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, "")


async def test_webhook_valid_secret_stores_update_and_message(
    silence_broker: list[dict[str, Any]],
) -> None:
    uow = FakeUnitOfWork(
        bot=make_bot(token_hash=TOKEN_HASH), telegram_user=make_telegram_user()
    )
    payload, raw = _update_payload()

    response = await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, TOKEN_HASH)

    assert response.success is True
    assert len(uow.telegram_updates.recorded) == 1
    stored = uow.telegram_updates.recorded[0]
    assert stored["update_id"] == 1
    assert stored["raw"] == raw
    assert stored["processed"] is True
    assert len(uow.messages.created) == 1
    assert uow.messages.created[0]["content"] == "hello"
    assert uow.commits == 1
    # New chat + the message itself are both broadcast.
    assert len(silence_broker) == 2


async def test_webhook_duplicate_update_is_not_reprocessed() -> None:
    uow = FakeUnitOfWork(
        bot=make_bot(token_hash=TOKEN_HASH),
        telegram_user=make_telegram_user(),
        update_is_new=False,
    )
    payload, raw = _update_payload()

    response = await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, TOKEN_HASH)

    assert response.success is True
    assert uow.messages.created == []
    assert uow.chats.created == []
    assert uow.commits == 1


async def test_webhook_disabled_bot_stores_update_without_processing() -> None:
    uow = FakeUnitOfWork(
        bot=make_bot(token_hash=TOKEN_HASH, status="disabled"),
        telegram_user=make_telegram_user(),
    )
    payload, raw = _update_payload()

    response = await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, TOKEN_HASH)

    assert response.success is True
    assert uow.telegram_updates.recorded[0]["processed"] is False
    assert uow.messages.created == []
    assert uow.commits == 1


async def test_webhook_non_message_update_is_stored_only() -> None:
    """Update types we do not act on are still logged verbatim."""
    uow = FakeUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))
    raw: dict[str, Any] = {
        "update_id": 7,
        "callback_query": {"id": "abc", "data": "ping"},
    }
    payload = TelegramUpdatePayload.model_validate(raw)

    response = await HandleWebhookUseCase(uow).execute(uuid4(), payload, raw, TOKEN_HASH)

    assert response.success is True
    assert uow.telegram_updates.recorded[0]["raw"] == raw
    assert uow.messages.created == []
    assert uow.commits == 1


# ----- POST /webhook/{bot_id}/bot-message ----- #


async def test_bot_message_unknown_bot_raises_not_found() -> None:
    uow = FakeUnitOfWork(bot=None)

    with pytest.raises(InstanceNotFoundException) as exc_info:
        await LogBotMessageUseCase(uow).execute(
            uuid4(), _bot_message_payload(), TOKEN_HASH
        )

    assert exc_info.value.code == ErrorCode.BOT_NOT_FOUND
    assert uow.messages.created == []


@pytest.mark.parametrize(
    "provided_token",
    ["", "c" * 64],
    ids=["missing-header", "wrong-hash"],
)
async def test_bot_message_invalid_secret_raises_forbidden(provided_token: str) -> None:
    uow = FakeUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH))

    with pytest.raises(AccessForbiddenException) as exc_info:
        await LogBotMessageUseCase(uow).execute(
            uuid4(), _bot_message_payload(), provided_token
        )

    assert exc_info.value.code == ErrorCode.AUTH_ACCESS_FORBIDDEN
    assert uow.messages.created == []
    assert uow.commits == 0


async def test_bot_message_unknown_telegram_user_raises_not_found() -> None:
    uow = FakeUnitOfWork(bot=make_bot(token_hash=TOKEN_HASH), telegram_user=None)

    with pytest.raises(InstanceNotFoundException) as exc_info:
        await LogBotMessageUseCase(uow).execute(
            uuid4(), _bot_message_payload(), TOKEN_HASH
        )

    assert exc_info.value.code == ErrorCode.AUTH_TELEGRAM_USER_NOT_FOUND


async def test_bot_message_disabled_bot_is_skipped() -> None:
    uow = FakeUnitOfWork(
        bot=make_bot(token_hash=TOKEN_HASH, status="disabled"),
        telegram_user=make_telegram_user(),
    )

    response = await LogBotMessageUseCase(uow).execute(
        uuid4(), _bot_message_payload(), TOKEN_HASH
    )

    assert response.success is True
    assert uow.messages.created == []
    assert uow.commits == 0


async def test_bot_message_valid_secret_logs_message(
    silence_broker: list[dict[str, Any]],
) -> None:
    uow = FakeUnitOfWork(
        bot=make_bot(token_hash=TOKEN_HASH),
        telegram_user=make_telegram_user(),
        chat=make_chat(),
    )

    response = await LogBotMessageUseCase(uow).execute(
        uuid4(), _bot_message_payload(), TOKEN_HASH
    )

    assert response.success is True
    assert len(uow.messages.created) == 1
    created = uow.messages.created[0]
    assert created["content"] == "Bot reply"
    assert created["tg_message_id"] == 42
    assert uow.commits == 1
    assert len(silence_broker) == 1
