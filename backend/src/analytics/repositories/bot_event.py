"""Event storage and the funnel report engine.

The report is one statement for any number of steps: a ``DISTINCT ON`` CTE
picking each user's first step-1 event, then one ``LEFT JOIN LATERAL`` per
later step, each taking that user's earliest matching event after the previous
one and inside the conversion window.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Select, func, literal, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.analytics.constants import (
    MAX_FUNNEL_STEPS,
    MAX_REPORT_RANGE,
    MAX_WINDOW_SECONDS,
    MIN_FUNNEL_STEPS,
    MIN_WINDOW_SECONDS,
)
from src.analytics.models import BotEvent
from src.core.database.repositories import BaseRepository


def _validate(
    steps: list[str],
    window: timedelta,
    since: datetime,
    until: datetime,
) -> None:
    """Re-check the guardrails the request schema already enforces.

    The schema cannot cover callers that build a report without going through
    the API, and a malformed ``steps`` JSONB read back from an old row would
    otherwise reach the planner.
    """
    if not MIN_FUNNEL_STEPS <= len(steps) <= MAX_FUNNEL_STEPS:
        raise ValueError(
            f"a funnel must have between {MIN_FUNNEL_STEPS} and "
            f"{MAX_FUNNEL_STEPS} steps, got {len(steps)}"
        )
    if any(not step for step in steps):
        raise ValueError("step names must be non-empty")

    window_seconds = window.total_seconds()
    if not MIN_WINDOW_SECONDS <= window_seconds <= MAX_WINDOW_SECONDS:
        raise ValueError(
            f"the conversion window must be between {MIN_WINDOW_SECONDS} and "
            f"{MAX_WINDOW_SECONDS} seconds, got {window_seconds:.0f}"
        )

    # Checked before the comparisons below, which would raise TypeError on a
    # mixed pair rather than say what is actually wrong.
    if since.tzinfo is None or until.tzinfo is None:
        raise ValueError("since and until must be timezone-aware")
    if until <= since:
        raise ValueError("until must be strictly after since")
    if until - since > MAX_REPORT_RANGE:
        raise ValueError(f"the report range must not exceed {MAX_REPORT_RANGE}")


def build_funnel_report_stmt(
    bot_id: UUID,
    steps: list[str],
    window: timedelta,
    since: datetime,
    until: datetime,
    *,
    include_timings: bool = True,
) -> Select[Any]:
    """Build the single-round-trip funnel aggregate for ``steps``.

    Returns a SELECT yielding exactly one row: ``entered_0 .. entered_{n-1}``,
    the distinct users reaching each step, and — when ``include_timings`` —
    ``median_1 .. median_{n-1}``, the median seconds from the previous step.

    Semantics, all deliberate:

    * First-touch. Per user we take the earliest step-1 event inside
      ``[since, until)``, then the earliest step-2 event after it, and so on.
      A user with no step-1 event is not in the funnel at all, which falls out
      for free because that CTE drives the whole statement.
    * The window is anchored to step 1, not to the previous step, so the whole
      journey is bounded by ``window`` rather than ``(n - 1) * window`` and
      every lateral gets the same constant upper bound.
    * Steps 2..n are *not* clipped at ``until``. A user who entered a minute
      before ``until`` is still allowed to convert afterwards; clipping would
      report a fake zero for the most recent cohort. Callers wanting a fully
      matured cohort shift ``until`` instead.
    * Ties break on ``(ts, id)``, not ``ts`` alone. ``id`` is a UUIDv7 and so
      is monotone by insertion. This is what makes a repeated step name work:
      plain ``>`` would drop same-timestamp pairs and ``>=`` would re-match the
      very same row.

    Raises:
        ValueError: If the step count, window or range violate the guardrails.
    """
    _validate(steps, window, since, until)

    horizon = literal(window, sa.Interval())

    # Funnel entry: each user's first occurrence of the first step.
    e0 = aliased(BotEvent, name="e0")
    entered = (
        select(
            e0.tg_user_id.label("tg_user_id"),
            e0.ts.label("ts_0"),
            e0.id.label("id_0"),
        )
        .where(
            e0.bot_id == bot_id,
            e0.name == steps[0],
            e0.ts >= since,
            e0.ts < until,
        )
        .distinct(e0.tg_user_id)
        .order_by(e0.tg_user_id, e0.ts, e0.id)
        .cte("entered")
    )

    from_obj: sa.FromClause = entered
    anchor_ts = entered.c.ts_0
    prev_ts: Any = entered.c.ts_0
    prev_id: Any = entered.c.id_0
    columns: list[Any] = [entered.c.tg_user_id, entered.c.ts_0]

    for position, step_name in enumerate(steps[1:], start=1):
        event = aliased(BotEvent, name=f"e{position}")
        step = (
            select(
                event.ts.label(f"ts_{position}"),
                event.id.label(f"id_{position}"),
            )
            .where(
                event.bot_id == bot_id,
                event.tg_user_id == entered.c.tg_user_id,
                event.name == step_name,
                tuple_(event.ts, event.id) > tuple_(prev_ts, prev_id),
                event.ts < anchor_ts + horizon,
            )
            .order_by(event.ts, event.id)
            .limit(1)
            .lateral(f"s{position}")
        )
        # LEFT, and ON TRUE: with ORDER BY ... LIMIT 1 the lateral yields zero
        # rows when the user did not convert, so an inner join would silently
        # collapse the funnel to converters only.
        from_obj = from_obj.join(step, sa.true(), isouter=True)
        prev_ts = step.c[f"ts_{position}"]
        prev_id = step.c[f"id_{position}"]
        columns.append(step.c[f"ts_{position}"])

    # One row per entrant, so a plain count() over each step column already is
    # the distinct-user count — no count(DISTINCT ...) needed. NULL propagates
    # down the chain on its own: comparing against a NULL previous step yields
    # no rows, so drop-off needs no explicit guard.
    matched = select(*columns).select_from(from_obj).cte("matched")

    aggregates: list[Any] = [
        func.count(matched.c[f"ts_{position}"]).label(f"entered_{position}")
        for position in range(len(steps))
    ]
    if include_timings:
        for position in range(1, len(steps)):
            gap = func.extract(
                "epoch",
                matched.c[f"ts_{position}"] - matched.c[f"ts_{position - 1}"],
            )
            aggregates.append(
                func.percentile_cont(0.5)
                .within_group(gap.asc())
                .label(f"median_{position}")
            )

    # No GROUP BY, so this returns exactly one row even with zero entrants:
    # every count 0, every median NULL.
    return select(*aggregates).select_from(matched)


class BotEventRepository(BaseRepository[BotEvent]):
    model = BotEvent

    async def bulk_insert(
        self, session: AsyncSession, values: list[dict[str, Any]]
    ) -> int:
        """Persist a batch of events in one statement.

        Returns:
            int: The number of rows written.
        """
        if not values:
            return 0
        await session.execute(pg_insert(self.model).values(values))
        return len(values)

    async def list_names(
        self,
        session: AsyncSession,
        bot_id: UUID,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[tuple[str, int]]:
        """Distinct event names a bot has actually sent, busiest first.

        This is what makes a funnel buildable: without it an operator types
        step names from memory, and a typo produces a silently empty funnel
        that looks exactly like a real zero-conversion one.

        Returns:
            list[tuple[str, int]]: ``(name, occurrences)`` pairs.
        """
        conditions: list[Any] = [self.model.bot_id == bot_id]
        if since is not None:
            conditions.append(self.model.ts >= since)

        stmt = (
            select(self.model.name, func.count())
            .where(*conditions)
            .group_by(self.model.name)
            .order_by(func.count().desc(), self.model.name)
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
        return [(str(name), int(count)) for name, count in rows]

    async def funnel_report(
        self,
        session: AsyncSession,
        bot_id: UUID,
        steps: list[str],
        window: timedelta,
        since: datetime,
        until: datetime,
        *,
        include_timings: bool = True,
    ) -> list[tuple[int, float | None]]:
        """Compute one funnel: per step, its user count and median gap.

        Cost is ``entrants x (len(steps) - 1)`` index probes against
        ``ix_bot_events_funnel`` plus the DISTINCT ON sort over the entry
        window. Past roughly half a million entrants the probes start to
        dominate and a set-based plan — one ``name = ANY(steps)`` scan with
        per-user window functions — wins; it fits behind this same signature.

        Returns:
            list[tuple[int, float | None]]: ``(users, median_seconds)`` per
            step, in funnel order. The median is None for the first step and
            wherever nobody converted.
        """
        stmt = build_funnel_report_stmt(
            bot_id, steps, window, since, until, include_timings=include_timings
        )
        row = (await session.execute(stmt)).one()._mapping

        report: list[tuple[int, float | None]] = []
        for position in range(len(steps)):
            median: float | None = None
            if include_timings and position > 0:
                raw_median = row[f"median_{position}"]
                median = None if raw_median is None else float(raw_median)
            report.append((int(row[f"entered_{position}"]), median))
        return report
