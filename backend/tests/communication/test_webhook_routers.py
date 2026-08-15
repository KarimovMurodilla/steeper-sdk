"""HTTP contract of the public webhook endpoints.

Complements the use-case tests by pinning how the router forwards the
``x-telegram-bot-api-secret-token`` header and how the registered exception
handlers translate the domain errors into 403 / 404 responses.
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.communication import routers
from src.communication.dependencies import (
    get_handle_webhook_use_case,
    get_log_bot_message_use_case,
)
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
)
from src.core.schemas import SuccessResponse
from src.main.presentation import include_exceptions_handlers

BOT_ID = uuid4()
UPDATE_BODY: dict[str, Any] = {
    "update_id": 1,
    "message": {
        "message_id": 42,
        "date": 1610000000,
        "text": "hello",
        "chat": {"id": 123456789, "type": "private"},
        "from": {"id": 123456789, "is_bot": False, "first_name": "John"},
    },
}
BOT_MESSAGE_BODY: dict[str, Any] = {
    "chat_id": 123456789,
    "text": "Bot reply",
    "message_id": 42,
    "date": 1610000000,
}


class RecordingUseCase:
    """Records what the router passed through, or raises a configured error."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def execute(self, bot_id: UUID, payload: Any, *args: Any) -> SuccessResponse:
        # handle_webhook takes (bot_id, payload, raw, secret); log_bot_message
        # takes (bot_id, payload, secret). The secret is always last.
        self.calls.append({"bot_id": bot_id, "secret": args[-1]})
        if self.error:
            raise self.error
        return SuccessResponse(success=True)


def _build_client(use_case: RecordingUseCase, dependency: Any) -> TestClient:
    app = FastAPI()
    app.include_router(routers.router)
    include_exceptions_handlers(app)
    app.dependency_overrides[dependency] = lambda: use_case
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("path", "body", "dependency"),
    [
        (f"/webhook/{BOT_ID}", UPDATE_BODY, get_handle_webhook_use_case),
        (
            f"/webhook/{BOT_ID}/bot-message",
            BOT_MESSAGE_BODY,
            get_log_bot_message_use_case,
        ),
    ],
    ids=["telegram-update", "bot-message"],
)
def test_endpoint_forwards_secret_header_and_returns_200(
    path: str, body: dict[str, Any], dependency: Any
) -> None:
    use_case = RecordingUseCase()
    client = _build_client(use_case, dependency)

    response = client.post(
        path, json=body, headers={"x-telegram-bot-api-secret-token": "s3cret"}
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert use_case.calls[0]["bot_id"] == BOT_ID
    assert use_case.calls[0]["secret"] == "s3cret"


@pytest.mark.parametrize(
    ("path", "body", "dependency"),
    [
        (f"/webhook/{BOT_ID}", UPDATE_BODY, get_handle_webhook_use_case),
        (
            f"/webhook/{BOT_ID}/bot-message",
            BOT_MESSAGE_BODY,
            get_log_bot_message_use_case,
        ),
    ],
    ids=["telegram-update", "bot-message"],
)
def test_endpoint_without_secret_header_passes_empty_string(
    path: str, body: dict[str, Any], dependency: Any
) -> None:
    """A missing header must reach the use case as "", which it always rejects."""
    use_case = RecordingUseCase()
    client = _build_client(use_case, dependency)

    response = client.post(path, json=body)

    assert response.status_code == 200
    assert use_case.calls[0]["secret"] == ""


@pytest.mark.parametrize(
    ("path", "body", "dependency"),
    [
        (f"/webhook/{BOT_ID}", UPDATE_BODY, get_handle_webhook_use_case),
        (
            f"/webhook/{BOT_ID}/bot-message",
            BOT_MESSAGE_BODY,
            get_log_bot_message_use_case,
        ),
    ],
    ids=["telegram-update", "bot-message"],
)
def test_endpoint_returns_403_on_invalid_secret(
    path: str, body: dict[str, Any], dependency: Any
) -> None:
    use_case = RecordingUseCase(
        error=AccessForbiddenException(ErrorCode.AUTH_ACCESS_FORBIDDEN)
    )
    client = _build_client(use_case, dependency)

    response = client.post(
        path, json=body, headers={"x-telegram-bot-api-secret-token": "wrong"}
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    ("path", "body", "dependency"),
    [
        (f"/webhook/{BOT_ID}", UPDATE_BODY, get_handle_webhook_use_case),
        (
            f"/webhook/{BOT_ID}/bot-message",
            BOT_MESSAGE_BODY,
            get_log_bot_message_use_case,
        ),
    ],
    ids=["telegram-update", "bot-message"],
)
def test_endpoint_returns_404_for_unknown_bot(
    path: str, body: dict[str, Any], dependency: Any
) -> None:
    use_case = RecordingUseCase(error=InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND))
    client = _build_client(use_case, dependency)

    response = client.post(
        path, json=body, headers={"x-telegram-bot-api-secret-token": "s3cret"}
    )

    assert response.status_code == 404


def test_webhook_rejects_malformed_payload() -> None:
    use_case = RecordingUseCase()
    client = _build_client(use_case, get_handle_webhook_use_case)

    response = client.post(
        f"/webhook/{BOT_ID}",
        json={"no_update_id": True},
        headers={"x-telegram-bot-api-secret-token": "s3cret"},
    )

    assert response.status_code == 422
    assert use_case.calls == []
