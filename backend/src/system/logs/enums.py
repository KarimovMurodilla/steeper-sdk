from enum import StrEnum


class LogLevel(StrEnum):
    """Standard ``logging`` levels captured from a bot process."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
