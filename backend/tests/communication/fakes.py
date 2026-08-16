"""In-memory doubles for the communication use-case tests.

The webhook use cases only ever touch the Unit of Work, so a small fake that
records the calls it receives is enough to exercise the authentication and
short-circuit branches without a database.
"""

from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4


class FakeSession:
    """Stands in for the SQLAlchemy AsyncSession used inside the use cases."""

    def __init__(self) -> None:
        self.flush_calls = 0

    async def flush(self) -> None:
        self.flush_calls += 1


class FakeBotRepository:
    def __init__(self, bot: Any) -> None:
        self._bot = bot
        self.calls: list[UUID] = []

    async def get_single(self, session: Any, **kwargs: Any) -> Any:
        self.calls.append(kwargs.get("id"))
        return self._bot


class FakeTelegramUpdateRepository:
    def __init__(self, is_new: bool = True) -> None:
        self._is_new = is_new
        self.recorded: list[dict[str, Any]] = []

    async def record(self, session: Any, data: dict[str, Any]) -> bool:
        self.recorded.append(data)
        return self._is_new


class FakeTelegramUserRepository:
    def __init__(self, user: Any = None) -> None:
        self._user = user
        self.upserts: list[dict[str, Any]] = []

    async def upsert(self, session: Any, bot_id: UUID, data: dict[str, Any]) -> Any:
        self.upserts.append(data)
        return self._user

    async def get_single(self, session: Any, **kwargs: Any) -> Any:
        return self._user


class FakeChatRepository:
    def __init__(self, chat: Any = None) -> None:
        self._chat = chat
        self.created: list[dict[str, Any]] = []

    async def get_by_tg_user(self, session: Any, bot_id: UUID, user_id: UUID) -> Any:
        return self._chat

    async def get_single(self, session: Any, **kwargs: Any) -> Any:
        return self._chat

    async def create(self, session: Any, data: dict[str, Any]) -> Any:
        self.created.append(data)
        self._chat = SimpleNamespace(id=uuid4(), **data)
        return self._chat


class FakeMessageRepository:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    async def create(self, session: Any, data: dict[str, Any]) -> Any:
        self.created.append(data)
        return SimpleNamespace(id=uuid4(), **data)


class FakeUnitOfWork:
    """Async-context-manager stand-in for ApplicationUnitOfWork."""

    def __init__(
        self,
        bot: Any = None,
        telegram_user: Any = None,
        chat: Any = None,
        update_is_new: bool = True,
    ) -> None:
        self.session = FakeSession()
        self.bots = FakeBotRepository(bot)
        self.telegram_updates = FakeTelegramUpdateRepository(update_is_new)
        self.telegram_users = FakeTelegramUserRepository(telegram_user)
        self.chats = FakeChatRepository(chat)
        self.messages = FakeMessageRepository()
        self.commits = 0

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1


def make_bot(token_hash: str = "a" * 64, status: str = "active") -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), token_hash=token_hash, status=status)


def make_telegram_user(tg_user_id: int = 123456789) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), tg_user_id=tg_user_id)


def make_chat() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4())
