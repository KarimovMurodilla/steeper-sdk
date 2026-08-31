from uuid import UUID

from loggers import get_logger
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import InstanceNotFoundException

logger = get_logger(__name__)


class DeleteBotUseCase:
    """Use case for deleting a Telegram Bot."""

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
    ) -> None:
        self.uow = uow

    async def execute(self, bot_id: UUID) -> None:
        """
        Executes the business logic for deleting a Telegram Bot.

        Args:
            bot_id (UUID): The unique identifier of the bot to delete.

        Returns:
            None

        Raises:
            InstanceNotFoundException: If the bot is not found.
        """
        async with self.uow as uow:
            bot = await uow.bots.get_single(uow.session, id=bot_id)
            if not bot:
                raise InstanceNotFoundException(ErrorCode.BOT_NOT_FOUND)

            await uow.bots.delete(uow.session, id=bot_id)
            await uow.commit()

        logger.info(f"Bot {bot_id} removed")
