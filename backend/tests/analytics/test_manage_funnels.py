"""CRUD over funnel definitions."""

from uuid import uuid4

import pytest

from src.analytics.schemas import FunnelCreate, FunnelUpdate
from src.analytics.usecases.manage_funnels import (
    CreateFunnelUseCase,
    DeleteFunnelUseCase,
    GetFunnelUseCase,
    ListFunnelsUseCase,
    UpdateFunnelUseCase,
)
from src.core.errors.exceptions import InstanceNotFoundException
from tests.analytics.fakes import FakeUnitOfWork, make_funnel

BOT_ID = uuid4()


def _payload(**overrides: object) -> FunnelCreate:
    data: dict[str, object] = {
        "name": "Onboarding",
        "steps": ["signup", "activated"],
        "window_seconds": 3600,
    }
    data.update(overrides)
    return FunnelCreate(**data)  # type: ignore[arg-type]


async def test_create_returns_the_stored_definition() -> None:
    uow = FakeUnitOfWork()
    use_case = CreateFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    result = await use_case.execute(BOT_ID, _payload())

    assert result.name == "Onboarding"
    assert result.steps == ["signup", "activated"]
    assert result.window_seconds == 3600
    assert uow.funnels.created[0]["bot_id"] == BOT_ID
    assert uow.commits == 1


async def test_create_reads_the_row_before_committing() -> None:
    # Regression: the use case used to commit and then refresh, which ends the
    # Unit of Work's transaction and then emits a statement inside it —
    # SQLAlchemy raises "Can't operate on closed transaction inside context
    # manager" and every create returns a 500.
    uow = FakeUnitOfWork()
    use_case = CreateFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    await use_case.execute(BOT_ID, _payload())

    assert uow.session.committed is True
    assert uow.session.refreshed == []


async def test_update_applies_only_the_fields_that_were_sent() -> None:
    funnel = make_funnel(bot_id=BOT_ID, name="Old", window_seconds=3600)
    uow = FakeUnitOfWork(funnel=funnel)
    use_case = UpdateFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    result = await use_case.execute(BOT_ID, funnel.id, FunnelUpdate(name="New"))

    assert result.name == "New"
    assert result.window_seconds == 3600
    assert uow.funnels.updated == [{"name": "New"}]


async def test_update_reads_the_row_before_committing() -> None:
    funnel = make_funnel(bot_id=BOT_ID)
    uow = FakeUnitOfWork(funnel=funnel)
    use_case = UpdateFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    await use_case.execute(BOT_ID, funnel.id, FunnelUpdate(name="New"))

    assert uow.session.refreshed == []


async def test_an_empty_update_is_not_an_error() -> None:
    funnel = make_funnel(bot_id=BOT_ID, name="Unchanged")
    uow = FakeUnitOfWork(funnel=funnel)
    use_case = UpdateFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    result = await use_case.execute(BOT_ID, funnel.id, FunnelUpdate())

    assert result.name == "Unchanged"
    assert uow.funnels.updated == []


async def test_updating_a_missing_funnel_is_a_404() -> None:
    uow = FakeUnitOfWork(funnel=None)
    use_case = UpdateFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    with pytest.raises(InstanceNotFoundException):
        await use_case.execute(BOT_ID, uuid4(), FunnelUpdate(name="New"))


async def test_get_and_list_return_the_bots_funnels() -> None:
    funnel = make_funnel(bot_id=BOT_ID, name="Onboarding")
    uow = FakeUnitOfWork(funnel=funnel)

    single = await GetFunnelUseCase(uow=uow).execute(BOT_ID, funnel.id)  # type: ignore[arg-type]
    listed = await ListFunnelsUseCase(uow=uow).execute(BOT_ID)  # type: ignore[arg-type]

    assert single.name == "Onboarding"
    assert [item.id for item in listed] == [funnel.id]


async def test_getting_a_missing_funnel_is_a_404() -> None:
    uow = FakeUnitOfWork(funnel=None)
    use_case = GetFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    with pytest.raises(InstanceNotFoundException):
        await use_case.execute(BOT_ID, uuid4())


async def test_delete_soft_deletes_and_commits() -> None:
    funnel = make_funnel(bot_id=BOT_ID)
    uow = FakeUnitOfWork(funnel=funnel)
    use_case = DeleteFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    result = await use_case.execute(BOT_ID, funnel.id)

    assert result.success is True
    assert uow.funnels.deleted == 1
    assert uow.commits == 1


async def test_deleting_a_missing_funnel_is_a_404() -> None:
    uow = FakeUnitOfWork(funnel=None)
    use_case = DeleteFunnelUseCase(uow=uow)  # type: ignore[arg-type]

    with pytest.raises(InstanceNotFoundException):
        await use_case.execute(BOT_ID, uuid4())
