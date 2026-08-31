"""Use case: the event names a bot has actually sent."""

from datetime import UTC, datetime
from uuid import UUID

from src.analytics.constants import EVENT_NAMES_LOOKBACK, MAX_EVENT_NAMES
from src.analytics.schemas import EventName
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork


class ListEventNamesUseCase:
    """
    Lists the distinct event names seen for a bot, busiest first.

    The funnel builder reads this: an operator picking from what the bot has
    really sent cannot produce the failure mode this feature is most prone to,
    a funnel whose steps name events that never existed and which therefore
    reports a flat zero indistinguishable from genuine non-conversion.
    """

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(self, bot_id: UUID) -> list[EventName]:
        """
        Executes the business logic for the event-name suggestion endpoint.

        Args:
            bot_id (UUID): The bot whose event vocabulary to list.

        Returns:
            list[EventName]: Names with their occurrence counts, busiest first.
        """
        since = datetime.now(UTC) - EVENT_NAMES_LOOKBACK
        async with self.uow as uow:
            rows = await uow.bot_events.list_names(
                uow.session, bot_id, since=since, limit=MAX_EVENT_NAMES
            )
        return [EventName(name=name, count=count) for name, count in rows]
