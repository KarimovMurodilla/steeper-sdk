from enum import StrEnum


class ChatStatus(StrEnum):
    OPEN = "open"  # Chat is active, bot/admin can respond
    CLOSED = "closed"  # Chat is closed (archived)
    BLOCKED = "blocked"  # User has blocked the bot

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls.__members__.values()}


class SenderType(StrEnum):
    USER = "user"  # Regular Telegram user
    BOT = "bot"  # Bot auto-reply
    ADMIN = "admin"  # Operator/admin response via dashboard
    SYSTEM = "system"  # System notification

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls.__members__.values()}


class MessageType(StrEnum):
    TEXT = "text"
    MEDIA = "media"  # Temporary general type for media messages
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    SYSTEM = "system"  # Service message (e.g., "Chat closed")

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls.__members__.values()}


class UpdateType(StrEnum):
    """Top-level type of an incoming Telegram Update.

    Mirrors the optional fields of the Telegram ``Update`` object. ``UNKNOWN``
    is used when none of the recognised fields are present (e.g. a brand-new
    update type Telegram introduces) so the raw payload is still retained.
    """

    MESSAGE = "message"
    EDITED_MESSAGE = "edited_message"
    CHANNEL_POST = "channel_post"
    EDITED_CHANNEL_POST = "edited_channel_post"
    CALLBACK_QUERY = "callback_query"
    INLINE_QUERY = "inline_query"
    CHOSEN_INLINE_RESULT = "chosen_inline_result"
    MY_CHAT_MEMBER = "my_chat_member"
    CHAT_MEMBER = "chat_member"
    CHAT_JOIN_REQUEST = "chat_join_request"
    MESSAGE_REACTION = "message_reaction"
    MESSAGE_REACTION_COUNT = "message_reaction_count"
    POLL = "poll"
    POLL_ANSWER = "poll_answer"
    PRE_CHECKOUT_QUERY = "pre_checkout_query"
    SHIPPING_QUERY = "shipping_query"
    UNKNOWN = "unknown"

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls.__members__.values()}


class ContentType(StrEnum):
    """Kind of content carried by a Telegram message-like update.

    Determined by which media/content field is present on the message object.
    ``TEXT`` covers plain text; ``UNKNOWN`` is a fallback for content we do not
    classify yet (the raw payload is still stored).
    """

    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    VIDEO_NOTE = "video_note"
    ANIMATION = "animation"
    AUDIO = "audio"
    VOICE = "voice"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    VENUE = "venue"
    CONTACT = "contact"
    POLL = "poll"
    DICE = "dice"
    SERVICE = "service"  # service/system message (new_chat_members, etc.)
    UNKNOWN = "unknown"

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls.__members__.values()}
