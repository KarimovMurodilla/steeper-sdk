"""HTTP contract of the funnel endpoints.

Pins how the ingestion router forwards the secret header, how the operator
routes are scoped to the bot from the path, and how the registered exception
handlers translate the domain errors into 400 / 403 / 404 responses.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.analytics.dependencies import (
    get_funnel_report_use_case,
    get_ingest_bot_events_use_case,
    get_list_event_names_use_case,
    get_list_funnels_use_case,
)
from src.analytics.routers import funnels
from src.analytics.schemas import (
    EventName,
    FunnelReport,
    FunnelStepReport,
    FunnelViewModel,
)
from src.bot.dependencies import require_bot
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    AccessForbiddenException,
    InstanceNotFoundException,
    InstanceProcessingException,
)
from src.core.schemas import SuccessResponse
from src.main.presentation import include_exceptions_handlers
from src.user.auth.dependencies import get_current_user

BOT_ID = uuid4()
FUNNEL_ID = uuid4()
NOW = datetime.now(UTC)
EVENT_BODY: dict[str, Any] = {
    "events": [
        {
            "name": "checkout_started",
            "tg_user_id": 123456789,
            "ts": "2026-05-01T12:00:00Z",
            "props": {"plan": "pro"},
        }
    ]
}


class RecordingIngestUseCase:
    """Records what the ingestion router passed through, or raises."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def execute(self, bot_id: UUID, payload: Any, secret: str) -> SuccessResponse:
        self.calls.append({"bot_id": bot_id, "secret": secret})
        if self.error:
            raise self.error
        return SuccessResponse(success=True)


class RecordingReportUseCase:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def execute(self, **kwargs: Any) -> FunnelReport:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return FunnelReport(
            funnel_id=FUNNEL_ID,
            name="Onboarding",
            window_seconds=3600,
            since=NOW,
            until=NOW,
            total_entered=0,
            steps=[
                FunnelStepReport(name="a", position=0, users=0),
                FunnelStepReport(name="b", position=1, users=0),
            ],
        )


class RecordingListUseCase:
    async def execute(self, bot_id: UUID) -> list[FunnelViewModel]:
        return [
            FunnelViewModel(
                id=FUNNEL_ID,
                bot_id=bot_id,
                name="Onboarding",
                steps=["a", "b"],
                window_seconds=3600,
                created_at=NOW,
                updated_at=NOW,
            )
        ]


def _returning(value: Any) -> Any:
    """Build a zero-argument override.

    The callable must take no parameters: FastAPI reads an override's signature
    the same way it reads an endpoint's, so a ``lambda value=value: value``
    would be treated as declaring a query parameter named ``value`` and the
    handler would receive a validated copy instead of the recording double.
    """

    def override() -> Any:
        return value

    return override


def _build_client(overrides: dict[Any, Any], *, authed: bool = True) -> TestClient:
    app = FastAPI()
    app.include_router(funnels.ingest_router, prefix="/communications/webhook")
    app.include_router(funnels.router, prefix="/bots")
    include_exceptions_handlers(app)
    for dependency, value in overrides.items():
        app.dependency_overrides[dependency] = _returning(value)
    if authed:
        app.dependency_overrides[get_current_user] = _returning(object())
        app.dependency_overrides[require_bot] = _returning(
            type("StubBot", (), {"id": BOT_ID})()
        )
    return TestClient(app, raise_server_exceptions=False)


def test_ingest_forwards_the_secret_header() -> None:
    use_case = RecordingIngestUseCase()
    client = _build_client({get_ingest_bot_events_use_case: use_case}, authed=False)

    response = client.post(
        f"/communications/webhook/{BOT_ID}/events",
        json=EVENT_BODY,
        headers={"x-telegram-bot-api-secret-token": "s3cret"},
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert use_case.calls[0] == {"bot_id": BOT_ID, "secret": "s3cret"}


def test_ingest_without_the_header_passes_an_empty_string() -> None:
    """A missing header must reach the use case as "", which it always rejects."""
    use_case = RecordingIngestUseCase()
    client = _build_client({get_ingest_bot_events_use_case: use_case}, authed=False)

    client.post(f"/communications/webhook/{BOT_ID}/events", json=EVENT_BODY)

    assert use_case.calls[0]["secret"] == ""


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (AccessForbiddenException(ErrorCode.AUTH_ACCESS_FORBIDDEN), 403),
        (InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND), 404),
    ],
    ids=["bad-secret", "unknown-bot"],
)
def test_ingest_translates_domain_errors(
    error: Exception, expected_status: int
) -> None:
    client = _build_client(
        {get_ingest_bot_events_use_case: RecordingIngestUseCase(error)}, authed=False
    )

    response = client.post(
        f"/communications/webhook/{BOT_ID}/events",
        json=EVENT_BODY,
        headers={"x-telegram-bot-api-secret-token": "wrong"},
    )

    assert response.status_code == expected_status


def test_ingest_rejects_an_oversized_batch() -> None:
    client = _build_client(
        {get_ingest_bot_events_use_case: RecordingIngestUseCase()}, authed=False
    )

    response = client.post(
        f"/communications/webhook/{BOT_ID}/events",
        json={
            "events": [
                {"name": "a", "tg_user_id": 1, "ts": "2026-05-01T12:00:00Z"}
                for _ in range(501)
            ]
        },
    )

    assert response.status_code == 422


def test_report_defaults_and_forwards_the_query_parameters() -> None:
    use_case = RecordingReportUseCase()
    client = _build_client({get_funnel_report_use_case: use_case})

    response = client.get(f"/bots/{BOT_ID}/funnels/{FUNNEL_ID}/report")

    assert response.status_code == 200
    call = use_case.calls[0]
    assert call["bot_id"] == BOT_ID
    assert call["funnel_id"] == FUNNEL_ID
    assert call["since"] is None and call["until"] is None
    # Off by default: it hides the most recent cohort entirely.
    assert call["mature_only"] is False
    assert call["include_timings"] is True


def test_report_passes_the_flags_through() -> None:
    use_case = RecordingReportUseCase()
    client = _build_client({get_funnel_report_use_case: use_case})

    client.get(
        f"/bots/{BOT_ID}/funnels/{FUNNEL_ID}/report",
        params={
            "since": "2026-04-01T00:00:00Z",
            "until": "2026-05-01T00:00:00Z",
            "mature_only": "true",
            "include_timings": "false",
        },
    )

    call = use_case.calls[0]
    assert call["since"] == datetime(2026, 4, 1, tzinfo=UTC)
    assert call["until"] == datetime(2026, 5, 1, tzinfo=UTC)
    assert call["mature_only"] is True
    assert call["include_timings"] is False


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (InstanceNotFoundException(ErrorCode.FUNNEL_NOT_FOUND), 404),
        (InstanceProcessingException(ErrorCode.FUNNEL_INVALID_DEFINITION), 400),
    ],
    ids=["missing-funnel", "bad-window"],
)
def test_report_translates_domain_errors(
    error: Exception, expected_status: int
) -> None:
    client = _build_client({get_funnel_report_use_case: RecordingReportUseCase(error)})

    response = client.get(f"/bots/{BOT_ID}/funnels/{FUNNEL_ID}/report")

    assert response.status_code == expected_status


def test_listing_funnels_is_scoped_to_the_bot_in_the_path() -> None:
    client = _build_client({get_list_funnels_use_case: RecordingListUseCase()})

    response = client.get(f"/bots/{BOT_ID}/funnels")

    assert response.status_code == 200
    assert response.json()[0]["bot_id"] == str(BOT_ID)


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "f", "steps": ["a"], "window_seconds": 3600},
        {"name": "f", "steps": ["a"] * 9, "window_seconds": 3600},
        {"name": "f", "steps": ["a", ""], "window_seconds": 3600},
        {"name": "f", "steps": ["a", "b"], "window_seconds": 30},
        {"name": "f", "steps": ["a", "b"], "window_seconds": 60 * 60 * 24 * 31},
    ],
    ids=[
        "too-few-steps",
        "too-many-steps",
        "empty-step",
        "window-too-short",
        "window-too-long",
    ],
)
def test_creating_an_invalid_funnel_is_rejected(payload: dict[str, Any]) -> None:
    client = _build_client({})

    response = client.post(f"/bots/{BOT_ID}/funnels", json=payload)

    assert response.status_code == 422


class RecordingNamesUseCase:
    def __init__(self) -> None:
        self.calls: list[UUID] = []

    async def execute(self, bot_id: UUID) -> list[EventName]:
        self.calls.append(bot_id)
        return [
            EventName(name="signup", count=120),
            EventName(name="pay", count=8),
        ]


def test_event_names_are_scoped_to_the_bot_in_the_path() -> None:
    use_case = RecordingNamesUseCase()
    client = _build_client({get_list_event_names_use_case: use_case})

    response = client.get(f"/bots/{BOT_ID}/events/names")

    assert response.status_code == 200
    assert use_case.calls == [BOT_ID]
    # Busiest first, so the builder's first suggestions are the useful ones.
    assert [row["name"] for row in response.json()] == ["signup", "pay"]
