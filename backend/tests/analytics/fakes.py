"""In-memory doubles for the analytics use-case tests.

The funnel use cases only ever reach the database through the Unit of Work, so
recording fakes are enough to exercise authentication, the clock-skew filter
and the conversion arithmetic without Postgres. What genuinely needs a database
— the LATERAL plan, the ``(ts, id)`` tiebreak — is covered by compiling the
statement in ``test_funnel_report_stmt.py`` and by the manual integration check
described in the plan.
"""

from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

from src.analytics.repositories.bot_event import build_funnel_report_stmt


class FakeSession:
    """Stands in for the SQLAlchemy AsyncSession used inside the use cases.

    Committing marks the session spent, and any later statement raises — the
    real Unit of Work opens a transaction in ``__aenter__`` and SQLAlchemy
    refuses to "operate on closed transaction inside context manager" once it
    is committed. Modelling that here is what keeps a use case from reading an
    ORM instance after the commit that ends its transaction.
    """

    def __init__(self) -> None:
        self.refreshed: list[Any] = []
        self.committed = False

    def _assert_open(self, operation: str) -> None:
        if self.committed:
            raise RuntimeError(
                f"cannot {operation} after commit: the transaction is closed"
            )

    async def flush(self) -> None:
        self._assert_open("flush")

    async def refresh(self, instance: Any) -> None:
        self._assert_open("refresh")
        self.refreshed.append(instance)


class FakeBotRepository:
    def __init__(self, bot: Any) -> None:
        self._bot = bot

    async def get_single(self, session: Any, **kwargs: Any) -> Any:
        return self._bot


class FakeTelegramUserRepository:
    def __init__(self, known: dict[int, UUID] | None = None) -> None:
        self._known = known or {}
        self.resolve_calls: list[list[int]] = []

    async def resolve_ids(
        self, session: Any, bot_id: UUID, tg_user_ids: Any
    ) -> dict[int, UUID]:
        self.resolve_calls.append(list(tg_user_ids))
        return {
            tg_user_id: self._known[tg_user_id]
            for tg_user_id in tg_user_ids
            if tg_user_id in self._known
        }


class FakeBotEventRepository:
    def __init__(self, report: list[tuple[int, float | None]] | None = None) -> None:
        self._report = report or []
        self.inserted: list[dict[str, Any]] = []
        self.report_calls: list[dict[str, Any]] = []

    async def bulk_insert(self, session: Any, values: list[dict[str, Any]]) -> int:
        self.inserted.extend(values)
        return len(values)

    async def funnel_report(
        self, session: Any, **kwargs: Any
    ) -> list[tuple[int, float | None]]:
        self.report_calls.append(kwargs)
        # Build the real statement and throw it away: the guardrails live in
        # the builder, and a fake that skipped them would let the use-case
        # tests pass on arguments the database would reject.
        build_funnel_report_stmt(
            kwargs["bot_id"],
            kwargs["steps"],
            kwargs["window"],
            kwargs["since"],
            kwargs["until"],
            include_timings=kwargs.get("include_timings", True),
        )
        return self._report


class FakeFunnelRepository:
    def __init__(self, funnel: Any = None) -> None:
        self._funnel = funnel
        self.created: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []
        self.deleted = 0

    async def get_single(self, session: Any, **kwargs: Any) -> Any:
        return self._funnel

    async def list_for_bot(self, session: Any, bot_id: UUID) -> list[Any]:
        return [self._funnel] if self._funnel else []

    async def create(self, session: Any, data: dict[str, Any]) -> Any:
        self.created.append(data)
        self._funnel = make_funnel(**data)
        return self._funnel

    async def update(self, session: Any, data: dict[str, Any], **filters: Any) -> Any:
        if self._funnel is None:
            return None
        self.updated.append(data)
        for key, value in data.items():
            setattr(self._funnel, key, value)
        return self._funnel

    async def delete(self, session: Any, **filters: Any) -> Any:
        if self._funnel is None:
            return None
        self.deleted += 1
        return self._funnel


class FakeUnitOfWork:
    """Async-context-manager stand-in for ApplicationUnitOfWork."""

    def __init__(
        self,
        bot: Any = None,
        funnel: Any = None,
        report: list[tuple[int, float | None]] | None = None,
        known_users: dict[int, UUID] | None = None,
    ) -> None:
        self.session = FakeSession()
        self.bots = FakeBotRepository(bot)
        self.telegram_users = FakeTelegramUserRepository(known_users)
        self.bot_events = FakeBotEventRepository(report)
        self.funnels = FakeFunnelRepository(funnel)
        self.commits = 0

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1
        self.session.committed = True


def make_bot(token_hash: str = "a" * 64) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), token_hash=token_hash, status="active")


def make_funnel(
    bot_id: UUID | None = None,
    name: str = "Onboarding",
    steps: list[str] | None = None,
    window_seconds: int = 3600,
    **extra: Any,
) -> SimpleNamespace:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return SimpleNamespace(
        id=extra.pop("id", uuid4()),
        bot_id=bot_id or uuid4(),
        name=name,
        steps=steps or ["a", "b", "c"],
        window_seconds=window_seconds,
        created_at=now,
        updated_at=now,
        is_deleted=False,
        deleted_at=None,
    )
