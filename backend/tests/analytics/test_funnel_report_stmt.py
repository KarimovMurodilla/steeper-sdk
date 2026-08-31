"""Shape of the generated funnel statement and its guardrails.

These compile the statement against the PostgreSQL dialect rather than running
it, because the properties that matter — a DISTINCT ON entry CTE, one LEFT JOIN
LATERAL per later step, and a window anchored to the first step — are all
visible in the SQL text and none of them need data to assert.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from src.analytics.repositories.bot_event import build_funnel_report_stmt

BOT_ID = uuid4()
UNTIL = datetime(2026, 5, 1, tzinfo=UTC)
SINCE = UNTIL - timedelta(days=7)
WINDOW = timedelta(hours=1)


def compile_stmt(steps: list[str], **kwargs: object) -> str:
    stmt = build_funnel_report_stmt(
        BOT_ID,
        steps,
        WINDOW,
        SINCE,
        UNTIL,
        **kwargs,  # type: ignore[arg-type]
    )
    return str(stmt.compile(dialect=postgresql.dialect()))


def test_entry_cte_picks_each_users_first_event() -> None:
    sql = compile_stmt(["a", "b"])
    assert "DISTINCT ON (e0.tg_user_id)" in sql
    assert "ORDER BY e0.tg_user_id, e0.ts, e0.id" in sql


def test_one_left_lateral_per_step_after_the_first() -> None:
    sql = compile_stmt(["a", "b", "c", "d"])
    # LEFT, not INNER: with ORDER BY ... LIMIT 1 the lateral yields no row at
    # all for a user who did not convert, so an inner join would quietly drop
    # every non-converter and report only the funnel's survivors.
    assert sql.count("LEFT OUTER JOIN LATERAL") == 3
    assert sql.count("LIMIT") == 3


def test_every_step_is_bounded_by_the_first_step_not_the_previous_one() -> None:
    sql = compile_stmt(["a", "b", "c"])
    # Each hop compares against its own predecessor...
    assert "(e1.ts, e1.id) > (entered.ts_0, entered.id_0)" in sql
    assert "(e2.ts, e2.id) > (s1.ts_1, s1.id_1)" in sql
    # ...but both windows are anchored to the entry timestamp, so the whole
    # journey is bounded by `window`, not by `(n - 1) * window`.
    assert sql.count("entered.ts_0 + %(param_1)s") == 2


def test_steps_are_ordered_by_ts_then_id() -> None:
    # The id tiebreak is what makes a repeated step name work when two events
    # share a timestamp: `>` alone would drop the pair, `>=` would re-match the
    # very same row.
    sql = compile_stmt(["a", "a"])
    assert "ORDER BY e1.ts, e1.id" in sql


def test_medians_are_computed_alongside_the_counts() -> None:
    sql = compile_stmt(["a", "b", "c"])
    assert sql.count("WITHIN GROUP") == 2
    assert (
        "WITHIN GROUP (ORDER BY EXTRACT(epoch FROM matched.ts_1 - matched.ts_0) ASC)"
        in sql
    )


def test_timings_can_be_skipped() -> None:
    sql = compile_stmt(["a", "b"], include_timings=False)
    assert "WITHIN GROUP" not in sql
    assert "count(matched.ts_1)" in sql


@pytest.mark.parametrize("steps", [["a"], ["a"] * 9])
def test_step_count_is_bounded(steps: list[str]) -> None:
    with pytest.raises(ValueError, match="between 2 and 8 steps"):
        compile_stmt(steps)


def test_empty_step_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        compile_stmt(["a", ""])


@pytest.mark.parametrize(
    "window", [timedelta(0), timedelta(seconds=30), timedelta(days=31)]
)
def test_window_is_bounded(window: timedelta) -> None:
    with pytest.raises(ValueError, match="conversion window"):
        build_funnel_report_stmt(BOT_ID, ["a", "b"], window, SINCE, UNTIL)


def test_inverted_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="strictly after"):
        build_funnel_report_stmt(BOT_ID, ["a", "b"], WINDOW, UNTIL, SINCE)


def test_range_is_capped() -> None:
    with pytest.raises(ValueError, match="report range"):
        build_funnel_report_stmt(
            BOT_ID, ["a", "b"], WINDOW, UNTIL - timedelta(days=200), UNTIL
        )


def test_naive_datetimes_are_rejected() -> None:
    # bot_events.ts is timestamptz; asyncpg misreads a naive value rather than
    # failing, which would silently shift every funnel by the server's offset.
    with pytest.raises(ValueError, match="timezone-aware"):
        build_funnel_report_stmt(
            BOT_ID, ["a", "b"], WINDOW, SINCE.replace(tzinfo=None), UNTIL
        )
