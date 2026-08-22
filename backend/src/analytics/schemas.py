from datetime import datetime
from enum import StrEnum

from pydantic import Field

from src.core.schemas import Base


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
    hour: int = Field(
        ..., ge=0, le=23, description="Hour of day in UTC", examples=[14]
    )
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
    updates: int = Field(..., description="Updates produced in the window", examples=[87])


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
