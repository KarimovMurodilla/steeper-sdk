"""Conversion arithmetic and window handling of the funnel report."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.analytics.usecases.get_funnel_report import GetFunnelReportUseCase
from src.core.errors.exceptions import (
    InstanceNotFoundException,
    InstanceProcessingException,
)
from tests.analytics.fakes import FakeUnitOfWork, make_funnel

BOT_ID = uuid4()
UNTIL = datetime(2026, 5, 1, tzinfo=UTC)
SINCE = UNTIL - timedelta(days=7)


def build(
    report: list[tuple[int, float | None]], window_seconds: int = 3600
) -> tuple[GetFunnelReportUseCase, FakeUnitOfWork, object]:
    funnel = make_funnel(bot_id=BOT_ID, window_seconds=window_seconds)
    uow = FakeUnitOfWork(funnel=funnel, report=report)
    return GetFunnelReportUseCase(uow=uow), uow, funnel  # type: ignore[arg-type]


async def test_conversions_are_relative_to_both_the_previous_and_first_step() -> None:
    use_case, _, funnel = build([(1000, None), (400, 60.0), (100, 300.0)])

    result = await use_case.execute(BOT_ID, funnel.id, since=SINCE, until=UNTIL)

    assert result.total_entered == 1000
    assert [step.users for step in result.steps] == [1000, 400, 100]
    assert result.steps[0].conversion_from_previous is None
    assert result.steps[0].conversion_from_first == 1.0
    assert result.steps[1].conversion_from_previous == 0.4
    assert result.steps[1].conversion_from_first == 0.4
    assert result.steps[2].conversion_from_previous == 0.25
    assert result.steps[2].conversion_from_first == 0.1
    assert result.steps[2].median_seconds_from_previous == 300.0


async def test_an_empty_funnel_reports_null_conversions_not_zero() -> None:
    # 0/0 is "no data". A dashboard rendering 0% for it would be a lie.
    use_case, _, funnel = build([(0, None), (0, None), (0, None)])

    result = await use_case.execute(BOT_ID, funnel.id, since=SINCE, until=UNTIL)

    assert result.total_entered == 0
    for step in result.steps:
        assert step.users == 0
        assert step.conversion_from_previous is None
        assert step.conversion_from_first is None
        assert step.median_seconds_from_previous is None


async def test_a_total_drop_off_reports_zero_conversion_then_null() -> None:
    use_case, _, funnel = build([(500, None), (0, None), (0, None)])

    result = await use_case.execute(BOT_ID, funnel.id, since=SINCE, until=UNTIL)

    # Step 2: real zero — 500 users entered and none converted.
    assert result.steps[1].conversion_from_previous == 0.0
    assert result.steps[1].conversion_from_first == 0.0
    # Step 3: no data — nobody reached step 2 to convert from.
    assert result.steps[2].conversion_from_previous is None
    assert result.steps[2].conversion_from_first == 0.0


async def test_steps_keep_the_funnels_names_and_order() -> None:
    use_case, _, funnel = build([(10, None), (5, 1.0), (1, 2.0)])

    result = await use_case.execute(BOT_ID, funnel.id, since=SINCE, until=UNTIL)

    assert [step.name for step in result.steps] == funnel.steps
    assert [step.position for step in result.steps] == [0, 1, 2]


async def test_the_default_window_is_the_last_thirty_days() -> None:
    use_case, uow, funnel = build([(1, None), (1, 0.0), (1, 0.0)])

    result = await use_case.execute(BOT_ID, funnel.id)

    assert result.until - result.since == timedelta(days=30)
    call = uow.bot_events.report_calls[0]
    assert call["since"].tzinfo is not None
    assert call["until"].tzinfo is not None


async def test_naive_bounds_are_treated_as_utc() -> None:
    use_case, uow, funnel = build([(1, None), (1, 0.0), (1, 0.0)])

    await use_case.execute(
        BOT_ID,
        funnel.id,
        since=SINCE.replace(tzinfo=None),
        until=UNTIL.replace(tzinfo=None),
    )

    call = uow.bot_events.report_calls[0]
    assert call["since"] == SINCE
    assert call["until"] == UNTIL


async def test_mature_only_pulls_the_entry_window_back_by_one_window() -> None:
    use_case, uow, funnel = build([(1, None), (1, 0.0), (1, 0.0)], window_seconds=7200)

    result = await use_case.execute(
        BOT_ID, funnel.id, since=SINCE, until=UNTIL, mature_only=True
    )

    assert result.until == UNTIL - timedelta(hours=2)
    assert uow.bot_events.report_calls[0]["until"] == UNTIL - timedelta(hours=2)


async def test_timings_can_be_skipped() -> None:
    use_case, uow, funnel = build([(1, None), (1, None), (1, None)])

    await use_case.execute(
        BOT_ID, funnel.id, since=SINCE, until=UNTIL, include_timings=False
    )

    assert uow.bot_events.report_calls[0]["include_timings"] is False


async def test_a_missing_funnel_is_a_404() -> None:
    uow = FakeUnitOfWork(funnel=None)
    use_case = GetFunnelReportUseCase(uow=uow)  # type: ignore[arg-type]

    with pytest.raises(InstanceNotFoundException):
        await use_case.execute(BOT_ID, uuid4(), since=SINCE, until=UNTIL)


async def test_an_impossible_window_is_a_400_not_a_crash() -> None:
    # mature_only against a long conversion window can close the entry window
    # entirely; that is the request's fault, not a server error.
    use_case, _, funnel = build(
        [(0, None)], window_seconds=int(timedelta(days=10).total_seconds())
    )

    with pytest.raises(InstanceProcessingException):
        await use_case.execute(
            BOT_ID,
            funnel.id,
            since=UNTIL - timedelta(days=2),
            until=UNTIL,
            mature_only=True,
        )
