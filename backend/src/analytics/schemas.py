from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.analytics.constants import (
    MAX_EVENT_BATCH,
    MAX_FUNNEL_STEPS,
    MAX_STEP_NAME_LENGTH,
    MAX_WINDOW_SECONDS,
    MIN_FUNNEL_STEPS,
    MIN_WINDOW_SECONDS,
)
from src.core.schemas import Base, IDSchema, TimestampSchema


class TimeGranularity(StrEnum):
    """Bucket size for time-series aggregation of Telegram updates."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class LabeledCount(Base):
    """A single category and its count (e.g. update_type -> count)."""

    label: str = Field(..., description="Category label", examples=["message"])
    count: int = Field(..., description="Number of updates", examples=[1200])


class TimeBucketCount(Base):
    """Number of updates within one time bucket."""

    bucket: datetime = Field(
        ..., description="Start of the time bucket", examples=["2026-05-29T00:00:00Z"]
    )
    count: int = Field(..., description="Updates in this bucket", examples=[87])


class HeatmapCell(Base):
    """Update volume for one (weekday, hour) cell of the activity heatmap."""

    weekday: int = Field(
        ...,
        ge=0,
        le=6,
        description="Day of week in UTC, 0 is Sunday and 6 is Saturday",
        examples=[3],
    )
    hour: int = Field(..., ge=0, le=23, description="Hour of day in UTC", examples=[14])
    count: int = Field(..., description="Updates in this cell", examples=[42])


class BotTrafficMetrics(Base):
    """Response for GET /bots/{bot_id}/metrics/traffic.

    Traffic shape of a bot over a ``[since, until)`` window: how much comes in,
    what kind of updates they are, where they come from, and when they peak.
    """

    total_updates: int = Field(
        ..., description="Total updates in the window", examples=[5400]
    )
    total_messages: int = Field(
        ..., description="Total stored messages in the window", examples=[4100]
    )
    total_chats: int = Field(
        ..., description="All-time chat sessions of this bot", examples=[302]
    )
    all_time_messages: int = Field(
        ..., description="All-time messages across all chats", examples=[45000]
    )
    by_update_type: list[LabeledCount] = Field(
        ..., description="Update counts grouped by update type"
    )
    by_content_type: list[LabeledCount] = Field(
        ..., description="Message-update counts grouped by content type"
    )
    by_chat_type: list[LabeledCount] = Field(
        ..., description="Update counts grouped by Telegram chat type"
    )
    by_sender_type: list[LabeledCount] = Field(
        ..., description="Message counts grouped by sender (user vs bot)"
    )
    timeseries: list[TimeBucketCount] = Field(
        ..., description="Update volume bucketed by the requested granularity"
    )
    heatmap: list[HeatmapCell] = Field(
        ..., description="Update volume per weekday and hour, non-empty cells only"
    )


class ActiveUserCounts(Base):
    """Rolling active-user counters, all relative to the request time."""

    dau: int = Field(..., description="Distinct users active in 1 day", examples=[150])
    wau: int = Field(..., description="Distinct users active in 7 days", examples=[720])
    mau: int = Field(
        ..., description="Distinct users active in 30 days", examples=[1900]
    )


class TopUser(Base):
    """One of the most active Telegram users of a bot."""

    tg_user_id: int = Field(..., description="Telegram user id", examples=[123456789])
    first_name: str | None = Field(
        None, description="First name, if known", examples=["Ali"]
    )
    username: str | None = Field(
        None, description="Telegram username, if set", examples=["ali"]
    )
    updates: int = Field(
        ..., description="Updates produced in the window", examples=[87]
    )


class BotAudienceMetrics(Base):
    """Response for GET /bots/{bot_id}/metrics/audience.

    Who the bot's users are and how engaged they stay. Growth and language
    breakdowns honour the ``[since, until)`` window; the rolling active-user
    counters and churn are always relative to the request time.
    """

    total_users: int = Field(
        ..., description="Total non-deleted users of this bot", examples=[1500]
    )
    new_users: int = Field(
        ..., description="Users first seen inside the window", examples=[210]
    )
    active: ActiveUserCounts = Field(..., description="Rolling active-user counters")
    churned_users: int = Field(
        ...,
        description="Known users with no update in the last 30 days",
        examples=[340],
    )
    new_users_timeseries: list[TimeBucketCount] = Field(
        ..., description="New users bucketed by the requested granularity"
    )
    by_language: list[LabeledCount] = Field(
        ..., description="User counts grouped by Telegram language code"
    )
    top_users: list[TopUser] = Field(
        ..., description="Most active users in the window, busiest first"
    )


class BotEventPayload(Base):
    """A single product event as reported by a bot process."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=MAX_STEP_NAME_LENGTH,
        description="Event name, used as a funnel step identifier",
        examples=["checkout_started"],
    )
    tg_user_id: int = Field(
        ...,
        description="Telegram id of the user the event belongs to",
        examples=[123456789],
    )
    ts: datetime = Field(
        ...,
        description="Bot-side timestamp of the event (Unix seconds or ISO-8601)",
        examples=[1700000000.123],
    )
    props: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured context attached to the event",
        examples=[{"plan": "pro", "amount": 4900}],
    )


class BotEventBatchPayload(Base):
    """Body of the event ingestion endpoint — one batch of events."""

    events: list[BotEventPayload] = Field(
        ...,
        min_length=1,
        max_length=MAX_EVENT_BATCH,
        description="Events, oldest first",
    )


class FunnelDefinitionMixin(BaseModel):
    """Shared validation for the ordered step list and the conversion window."""

    @field_validator("steps", check_fields=False)
    @classmethod
    def _validate_steps(cls, value: list[str]) -> list[str]:
        if not MIN_FUNNEL_STEPS <= len(value) <= MAX_FUNNEL_STEPS:
            raise ValueError(
                f"a funnel must have between {MIN_FUNNEL_STEPS} and "
                f"{MAX_FUNNEL_STEPS} steps"
            )
        for step in value:
            if not step or len(step) > MAX_STEP_NAME_LENGTH:
                raise ValueError(
                    "step names must be non-empty and at most "
                    f"{MAX_STEP_NAME_LENGTH} characters"
                )
        return value


class FunnelCreate(Base, FunnelDefinitionMixin):
    """Body of POST /bots/{bot_id}/funnels."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable funnel name",
        examples=["Onboarding to first payment"],
    )
    steps: list[str] = Field(
        ...,
        description=(
            "Ordered event names. Repeating a name is allowed and means the "
            "user did it again after the previous step."
        ),
        examples=[["onboarding_started", "onboarding_finished", "payment_succeeded"]],
    )
    window_seconds: int = Field(
        ...,
        ge=MIN_WINDOW_SECONDS,
        le=MAX_WINDOW_SECONDS,
        description=(
            "Conversion window, measured from the first step. Every later step "
            "must happen within it for the user to count as converted."
        ),
        examples=[86400],
    )


class FunnelUpdate(Base, FunnelDefinitionMixin):
    """Body of PATCH /bots/{bot_id}/funnels/{funnel_id} — all fields optional."""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="New funnel name"
    )
    steps: list[str] | None = Field(None, description="New ordered event names")
    window_seconds: int | None = Field(
        None,
        ge=MIN_WINDOW_SECONDS,
        le=MAX_WINDOW_SECONDS,
        description="New conversion window in seconds",
    )


class FunnelViewModel(IDSchema, TimestampSchema):
    """A stored funnel definition as returned to the operator panel."""

    bot_id: UUID = Field(..., description="Bot this funnel belongs to")
    name: str = Field(..., description="Funnel name", examples=["Onboarding"])
    steps: list[str] = Field(..., description="Ordered event names")
    window_seconds: int = Field(
        ..., description="Conversion window in seconds", examples=[86400]
    )


class FunnelStepReport(Base):
    """One step of a computed funnel."""

    name: str = Field(
        ..., description="Event name of this step", examples=["payment_succeeded"]
    )
    position: int = Field(
        ..., ge=0, description="Zero-based position in the funnel", examples=[2]
    )
    users: int = Field(
        ..., description="Distinct users who reached this step", examples=[142]
    )
    conversion_from_previous: float | None = Field(
        None,
        description=(
            "Share of the previous step's users who reached this one, 0..1. "
            "Null for the first step and whenever the previous step had no "
            "users — no data, not zero percent."
        ),
        examples=[0.42],
    )
    conversion_from_first: float | None = Field(
        None,
        description="Share of funnel entrants who reached this step, 0..1",
        examples=[0.11],
    )
    median_seconds_from_previous: float | None = Field(
        None,
        description=(
            "Median time from the previous step, in seconds. Null for the "
            "first step, when nobody converted, or when timings were not "
            "requested."
        ),
        examples=[734.5],
    )


class FunnelReport(Base):
    """Response for GET /bots/{bot_id}/funnels/{funnel_id}/report."""

    funnel_id: UUID = Field(..., description="Funnel that was computed")
    name: str = Field(..., description="Funnel name")
    window_seconds: int = Field(..., description="Conversion window applied")
    since: datetime = Field(
        ..., description="Inclusive start of the entry window actually used"
    )
    until: datetime = Field(
        ..., description="Exclusive end of the entry window actually used"
    )
    total_entered: int = Field(
        ..., description="Distinct users who performed the first step", examples=[1280]
    )
    steps: list[FunnelStepReport] = Field(
        ..., description="One entry per funnel step, in order"
    )


class EventName(Base):
    """One event name a bot has sent, with how often it occurred."""

    name: str = Field(..., description="Event name", examples=["checkout_started"])
    count: int = Field(
        ..., description="Occurrences in the lookback window", examples=[1280]
    )
