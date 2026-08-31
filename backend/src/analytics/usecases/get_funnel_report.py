"""Use case: compute a stored funnel over a time window."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.analytics.constants import DEFAULT_REPORT_RANGE
from src.analytics.models import Funnel
from src.analytics.schemas import FunnelReport, FunnelStepReport
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import (
    InstanceNotFoundException,
    InstanceProcessingException,
)


def _normalize_window(
    since: datetime | None, until: datetime | None
) -> tuple[datetime, datetime]:
    """Fill in defaults and force UTC.

    ``bot_events.ts`` is ``timestamptz`` and asyncpg misreads naive datetimes,
    so no naive value may reach the query builder.
    """
    resolved_until = until or datetime.now(UTC)
    resolved_since = since or (resolved_until - DEFAULT_REPORT_RANGE)

    if resolved_until.tzinfo is None:
        resolved_until = resolved_until.replace(tzinfo=UTC)
    if resolved_since.tzinfo is None:
        resolved_since = resolved_since.replace(tzinfo=UTC)

    return resolved_since.astimezone(UTC), resolved_until.astimezone(UTC)


class GetFunnelReportUseCase:
    """
    Turns a stored funnel definition into per-step counts and conversions.

    The matching itself happens in one statement in ``BotEventRepository``;
    this use case owns the window defaults and the conversion arithmetic, which
    stays in Python so that "nobody reached the previous step" serializes as
    null rather than as a zero-percent conversion.
    """

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(
        self,
        bot_id: UUID,
        funnel_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
        mature_only: bool = False,
        include_timings: bool = True,
    ) -> FunnelReport:
        """
        Executes the business logic for the funnel report endpoint.

        Args:
            bot_id (UUID): The bot the funnel belongs to.
            funnel_id (UUID): The funnel to compute.
            since (datetime | None): Inclusive lower bound of the entry window.
            until (datetime | None): Exclusive upper bound of the entry window.
            mature_only (bool): Admit only entrants who have had a full
                conversion window, by pulling the entry window's end back by
                ``window_seconds``. Off by default, because it hides the most
                recent cohort entirely.
            include_timings (bool): Compute median time between steps.

        Returns:
            FunnelReport: Per-step users, conversions and median gaps.

        Raises:
            InstanceNotFoundException: If the funnel does not exist on this bot.
            InstanceProcessingException: If the window or the stored definition
                is out of bounds.
        """
        window_since, window_until = _normalize_window(since, until)

        async with self.uow as uow:
            funnel: Funnel | None = await uow.funnels.get_single(
                uow.session, id=funnel_id, bot_id=bot_id
            )
            if funnel is None:
                raise InstanceNotFoundException(ErrorCode.FUNNEL_NOT_FOUND)

            # Read everything off the row before leaving the session: the
            # report is assembled after it closes.
            funnel_name = funnel.name
            window_seconds = funnel.window_seconds
            step_names = list(funnel.steps)

            window = timedelta(seconds=window_seconds)
            entry_until = window_until - window if mature_only else window_until

            try:
                rows = await uow.bot_events.funnel_report(
                    uow.session,
                    bot_id=bot_id,
                    steps=step_names,
                    window=window,
                    since=window_since,
                    until=entry_until,
                    include_timings=include_timings,
                )
            except ValueError as exc:
                # Either the caller asked for an impossible window, or
                # ``mature_only`` pulled the entry window shut against a long
                # conversion window. Both are the request's fault, not ours.
                raise InstanceProcessingException(
                    ErrorCode.FUNNEL_INVALID_DEFINITION
                ) from exc

        entered = rows[0][0]
        steps = [
            FunnelStepReport(
                name=name,
                position=position,
                users=users,
                # 0/0 is "no data", not a zero-percent conversion. A dashboard
                # rendering 0% for an empty funnel is a lie.
                conversion_from_previous=(
                    users / rows[position - 1][0]
                    if position and rows[position - 1][0]
                    else None
                ),
                conversion_from_first=(users / entered if entered else None),
                median_seconds_from_previous=median,
            )
            for position, (name, (users, median)) in enumerate(
                zip(step_names, rows, strict=True)
            )
        ]

        return FunnelReport(
            funnel_id=funnel_id,
            name=funnel_name,
            window_seconds=window_seconds,
            since=window_since,
            until=entry_until,
            total_entered=entered,
            steps=steps,
        )
