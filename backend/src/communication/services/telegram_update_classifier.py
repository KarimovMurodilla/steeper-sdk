"""Stateless classification of raw Telegram updates.

Given the verbatim JSON of a Telegram ``Update``, derive the flat analytics
dimensions (update type, content type, user/chat ids, timestamp) that are
stored alongside the raw payload in ``telegram_updates``. This is pure logic
with no I/O so it can be unit-tested in isolation and reused by the webhook
use case.

Returns plain ``UpdateType`` / ``ContentType`` enum members (not a Pydantic
schema) so the values can be handed straight to SQLAlchemy's ``Enum`` column,
which stores enum member names — bypassing the project ``Base`` schema's
``use_enum_values`` coercion that would otherwise emit the lowercase values.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from src.communication.enums import ContentType, UpdateType

# Update key (on the Telegram Update object) -> our UpdateType.
_MESSAGE_LIKE_KEYS: dict[str, UpdateType] = {
    "message": UpdateType.MESSAGE,
    "edited_message": UpdateType.EDITED_MESSAGE,
    "channel_post": UpdateType.CHANNEL_POST,
    "edited_channel_post": UpdateType.EDITED_CHANNEL_POST,
}

_UPDATE_KEY_MAP: dict[str, UpdateType] = {
    **_MESSAGE_LIKE_KEYS,
    "callback_query": UpdateType.CALLBACK_QUERY,
    "inline_query": UpdateType.INLINE_QUERY,
    "chosen_inline_result": UpdateType.CHOSEN_INLINE_RESULT,
    "my_chat_member": UpdateType.MY_CHAT_MEMBER,
    "chat_member": UpdateType.CHAT_MEMBER,
    "chat_join_request": UpdateType.CHAT_JOIN_REQUEST,
    "message_reaction": UpdateType.MESSAGE_REACTION,
    "message_reaction_count": UpdateType.MESSAGE_REACTION_COUNT,
    "poll": UpdateType.POLL,
    "poll_answer": UpdateType.POLL_ANSWER,
    "pre_checkout_query": UpdateType.PRE_CHECKOUT_QUERY,
    "shipping_query": UpdateType.SHIPPING_QUERY,
}

# Ordered: more specific fields first (e.g. animation/video_note before
# video/document) because Telegram sets overlapping fields on some messages.
_CONTENT_FIELD_MAP: tuple[tuple[str, ContentType], ...] = (
    ("text", ContentType.TEXT),
    ("photo", ContentType.PHOTO),
    ("animation", ContentType.ANIMATION),
    ("sticker", ContentType.STICKER),
    ("video_note", ContentType.VIDEO_NOTE),
    ("video", ContentType.VIDEO),
    ("voice", ContentType.VOICE),
    ("audio", ContentType.AUDIO),
    ("document", ContentType.DOCUMENT),
    ("location", ContentType.LOCATION),
    ("venue", ContentType.VENUE),
    ("contact", ContentType.CONTACT),
    ("poll", ContentType.POLL),
    ("dice", ContentType.DICE),
)

# Presence of any of these fields marks a service/system message.
_SERVICE_FIELDS: frozenset[str] = frozenset(
    {
        "new_chat_members",
        "left_chat_member",
        "new_chat_title",
        "new_chat_photo",
        "delete_chat_photo",
        "group_chat_created",
        "supergroup_chat_created",
        "channel_chat_created",
        "migrate_to_chat_id",
        "migrate_from_chat_id",
        "pinned_message",
        "successful_payment",
        "video_chat_started",
        "video_chat_ended",
        "video_chat_participants_invited",
    }
)


@dataclass(frozen=True)
class ClassifiedUpdate:
    """Flat analytics dimensions extracted from a raw Telegram update."""

    update_type: UpdateType
    tg_user_id: int | None
    tg_chat_id: int | None
    chat_type: str | None
    content_type: ContentType | None
    tg_date: datetime | None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _detect_content_type(message: dict[str, Any]) -> ContentType:
    for field, content_type in _CONTENT_FIELD_MAP:
        if message.get(field) is not None:
            return content_type
    if any(field in message for field in _SERVICE_FIELDS):
        return ContentType.SERVICE
    return ContentType.UNKNOWN


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return None


def classify_update(raw: dict[str, Any]) -> ClassifiedUpdate:
    """Classify a raw Telegram update into stored analytics dimensions.

    Never raises on unexpected shapes: anything unrecognised yields
    ``UpdateType.UNKNOWN`` with null dimensions so the raw payload is still
    retained for later inspection.
    """
    payload_key = next((key for key in _UPDATE_KEY_MAP if key in raw), None)
    if payload_key is None:
        return ClassifiedUpdate(
            update_type=UpdateType.UNKNOWN,
            tg_user_id=None,
            tg_chat_id=None,
            chat_type=None,
            content_type=None,
            tg_date=None,
        )

    update_type = _UPDATE_KEY_MAP[payload_key]
    payload = _as_dict(raw[payload_key])

    # User: most updates carry "from" (aiogram serialises it as "from_user");
    # reactions/poll answers use "user".
    sender = _as_dict(
        payload.get("from") or payload.get("from_user") or payload.get("user")
    )
    tg_user_id = sender.get("id")

    # Chat: directly on the payload, or nested under callback_query.message.
    chat = _as_dict(payload.get("chat"))
    if not chat:
        chat = _as_dict(_as_dict(payload.get("message")).get("chat"))
    tg_chat_id = chat.get("id")
    chat_type = chat.get("type")

    content_type = (
        _detect_content_type(payload) if payload_key in _MESSAGE_LIKE_KEYS else None
    )
    tg_date = _to_datetime(payload.get("date"))

    return ClassifiedUpdate(
        update_type=update_type,
        tg_user_id=tg_user_id if isinstance(tg_user_id, int) else None,
        tg_chat_id=tg_chat_id if isinstance(tg_chat_id, int) else None,
        chat_type=chat_type if isinstance(chat_type, str) else None,
        content_type=content_type,
        tg_date=tg_date,
    )
