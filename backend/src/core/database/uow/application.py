from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.repositories.bot import BotRepository
from src.communication.repositories.chat import ChatRepository
from src.communication.repositories.message import MessageRepository
from src.communication.repositories.telegram_update import TelegramUpdateRepository
from src.core.database.repositories import BaseRepository
from src.core.database.uow.abstract import R, RepositoryProtocol
from src.core.database.uow.sqlalchemy import RepositoryInstance, SQLAlchemyUnitOfWork
from src.crm.repositories import TelegramUserRepository
from src.marketing.repositories.broadcast import BroadcastRepository
from src.marketing.repositories.broadcast_delivery import BroadcastDeliveryRepository
from src.user.repositories import UserRepository


class ApplicationUnitOfWork(SQLAlchemyUnitOfWork[R]):
    """
    Application-specific Unit of Work implementation.

    This class extends SQLAlchemyUnitOfWork and provides repository factory methods
    for all repositories used in the application.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the ApplicationUnitOfWork with a SQLAlchemy session.

        Args:
            session: The SQLAlchemy AsyncSession to use for database operations
        """
        super().__init__(session)
        self._repositories: dict[type[BaseRepository[Any]], BaseRepository[Any]] = {}

    def _get_repository(
        self, repository_type: type[RepositoryInstance]
    ) -> RepositoryInstance:
        """
        Get or create a repository of the specified type.

        This method implements a caching mechanism for repositories
        to avoid creating multiple instances of the same repository.

        Args:
            repository_type: The repository class to get or create

        Returns:
            An instance of the specified repository type
        """
        if repository_type not in self._repositories:
            self._repositories[repository_type] = repository_type()

        return cast(RepositoryInstance, self._repositories[repository_type])

    @property
    def users(self) -> UserRepository:
        """
        Get the UserRepository.

        Returns:
            UserRepository: The user repository
        """
        return self._get_repository(UserRepository)

    @property
    def bots(self) -> BotRepository:
        return self._get_repository(BotRepository)

    @property
    def chats(self) -> ChatRepository:
        return self._get_repository(ChatRepository)

    @property
    def messages(self) -> MessageRepository:
        return self._get_repository(MessageRepository)

    @property
    def telegram_users(self) -> TelegramUserRepository:
        return self._get_repository(TelegramUserRepository)

    @property
    def telegram_updates(self) -> TelegramUpdateRepository:
        return self._get_repository(TelegramUpdateRepository)

    @property
    def broadcasts(self) -> BroadcastRepository:
        return self._get_repository(BroadcastRepository)

    @property
    def broadcast_deliveries(self) -> BroadcastDeliveryRepository:
        return self._get_repository(BroadcastDeliveryRepository)


async def get_uow(session: AsyncSession) -> ApplicationUnitOfWork[RepositoryProtocol]:
    """
    Dependency injection function to get an ApplicationUnitOfWork instance.

    Args:
        session: The SQLAlchemy AsyncSession to use for database operations

    Returns:
        ApplicationUnitOfWork: The Unit of Work instance
    """
    return ApplicationUnitOfWork(session)
