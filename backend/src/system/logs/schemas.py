from datetime import datetime
from typing import Any

from pydantic import Field

from src.core.schemas import Base
from src.system.logs.enums import LogLevel


class BotLogRecordPayload(Base):
    """A single ``logging.LogRecord`` as shipped by the ``steeper`` library."""

    ts: datetime = Field(
        ...,
        description="Bot-side timestamp of the record (Unix seconds or ISO-8601)",
        examples=[1700000000.123],
    )
    level: LogLevel = Field(
        ..., description="Log level name", examples=[LogLevel.ERROR]
    )
    logger: str = Field(
        ...,
        max_length=255,
        description="Name of the logger that emitted the record",
        examples=["app.handlers.start"],
    )
    message: str = Field(
        ...,
        description="Formatted log message",
        examples=["Failed to answer callback query"],
    )
    module: str | None = Field(
        None, max_length=255, description="Module name", examples=["handlers"]
    )
    func: str | None = Field(
        None, max_length=255, description="Function name", examples=["cmd_start"]
    )
    line: int | None = Field(
        None, ge=0, description="Source line number", examples=[42]
    )
    exc: str | None = Field(
        None,
        description="Formatted traceback, when the record carried exception info",
        examples=["Traceback (most recent call last): ..."],
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured context attached to the record",
    )


class BotLogBatchPayload(Base):
    """Body of the log ingestion endpoint — one batch of records."""

    records: list[BotLogRecordPayload] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Log records, oldest first",
    )


class BotLogViewModel(Base):
    """A stored log record as returned to the operator panel.

    Loki has no row identity, so records are addressed by their timestamp: the
    nanosecond value is both the pagination cursor and, combined with the
    message, the panel's de-duplication key.
    """

    cursor: str = Field(
        ...,
        description=(
            "Record timestamp in Unix nanoseconds. Pass the last item's value "
            "as the `cursor` query parameter to fetch the next page."
        ),
        examples=["1700000000123000000"],
    )
    ts: datetime = Field(
        ...,
        description="Bot-side timestamp of the record",
        examples=["2026-01-01T12:00:00Z"],
    )
    level: LogLevel = Field(
        ..., description="Log level name", examples=[LogLevel.ERROR]
    )
    logger: str = Field(..., description="Logger name", examples=["app.handlers.start"])
    message: str = Field(..., description="Formatted log message", examples=["Boom"])
    module: str | None = Field(None, description="Module name", examples=["handlers"])
    func: str | None = Field(None, description="Function name", examples=["cmd_start"])
    line: int | None = Field(None, description="Source line number", examples=[42])
    exc: str | None = Field(None, description="Formatted traceback, if any")
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Structured context attached to the record"
    )


class WSBotLogCreatedData(Base):
    """Payload data for the ``bot.log.created`` realtime event.

    A whole ingested batch is pushed as one frame — log traffic is orders of
    magnitude denser than chat traffic, so one frame per record would flood the
    socket.
    """

    records: list[BotLogViewModel] = Field(
        ..., description="Newly stored log records, oldest first"
    )
