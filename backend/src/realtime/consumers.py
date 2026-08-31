from typing import Any

from faststream.rabbit import RabbitQueue

from loggers import get_logger
from src.realtime.broker import broker, steeper_exchange
from src.realtime.dependencies import get_connection_manager
from src.realtime.enums import EventType

logger = get_logger(__name__)

# Dynamic queue — each WS gateway instance gets its own exclusive queue
events_queue = RabbitQueue(
    name="",
    routing_key="bot.*.#",
    exclusive=True,
    auto_delete=True,
)


@broker.subscriber(
    queue=events_queue,
    exchange=steeper_exchange,
)
async def handle_realtime_event(body: dict[str, Any]) -> None:
    """
    FastStream subscriber that listens for all chat-related events.
    Broadcasts the event to clients subscribed to the specific chat OR the entire bot.
    """
    chat_id = body.get("chat_id")
    bot_id = body.get("bot_id")
    event = body.get("event")

    # Log batches go only to clients that explicitly subscribed to the log
    # stream — routing them through the generic bot broadcast would flood every
    # open panel with traffic it never asked for.
    if event == EventType.BOT_LOG_CREATED:
        if not bot_id:
            logger.warning("Received log event without bot_id, skipping")
            return
        await get_connection_manager().broadcast_logs(str(bot_id), body)
        logger.debug("Broadcasted log event to bot %s log subscribers", bot_id)
        return

    if not chat_id and not bot_id:
        logger.warning("Received event without chat_id or bot_id, skipping: %s", body)
        return

    manager = get_connection_manager()

    # Broadcast to both targets.
    # Manager will ensure no duplicates are sent using a Set union.
    await manager.broadcast(
        chat_id=str(chat_id) if chat_id else None,
        bot_id=str(bot_id) if bot_id else None,
        message=body,
    )

    logger.debug("Broadcasted event to chat %s and bot %s", chat_id, bot_id)
