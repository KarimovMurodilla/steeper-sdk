from enum import StrEnum


class BotStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls.__members__.values()}
