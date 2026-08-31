from enum import StrEnum


class EventType(StrEnum):
    CHAT_MESSAGE_CREATED = "chat.message.created"
    CHAT_MESSAGE_UPDATED = "chat.message.updated"
    CHAT_MESSAGE_DELETED = "chat.message.deleted"
    CHAT_CREATED = "chat.created"
    CHAT_TYPING = "chat.typing"
    BOT_LOG_CREATED = "bot.log.created"
    ERROR = "system.error"


class WSAction(StrEnum):
    AUTHENTICATE = "authenticate"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    TYPING = "typing"
    PING = "ping"


class WSTopic(StrEnum):
    """Opt-in event streams a client can subscribe to on top of a bot_id."""

    LOGS = "logs"
