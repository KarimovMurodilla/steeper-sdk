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


class BotUpdateStats(Base):
    """Response for GET /bots/{bot_id}/analytics/updates.

    Aggregations are computed from the raw ``telegram_updates`` log, optionally
    constrained to a ``[since, until)`` window over Telegram's own timestamp.
    """

    total: int = Field(
        ..., description="Total updates in the window", examples=[5400]
    )
    active_users: int = Field(
        ...,
        description="Distinct Telegram users that produced any update",
        examples=[420],
    )
    by_type: list[LabeledCount] = Field(
        ..., description="Update counts grouped by update type"
    )
    by_content_type: list[LabeledCount] = Field(
        ..., description="Message-update counts grouped by content type"
    )
    timeseries: list[TimeBucketCount] = Field(
        ..., description="Update volume bucketed by the requested granularity"
    )


class BotAnalyticsSummary(Base):
    """Response for GET /bots/{bot_id}/analytics/summary."""

    users: int = Field(
        ..., description="Total unique Telegram users of this bot", examples=[1500]
    )
    chats: int = Field(..., description="Total chat sessions", examples=[302])
    messages: int = Field(
        ..., description="Total messages in all chats", examples=[45000]
    )
    dau: int = Field(
        ...,
        description="Daily active users (sent/received a message today)",
        examples=[150],
    )
