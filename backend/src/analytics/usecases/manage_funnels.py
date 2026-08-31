"""Use cases: operator CRUD over funnel definitions.

They are grouped in one module because each is a handful of lines over the same
repository; splitting them into five files would say more about the file count
than about the code.
"""

from uuid import UUID

from src.analytics.models import Funnel
from src.analytics.schemas import FunnelCreate, FunnelUpdate, FunnelViewModel
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork
from src.core.errors.enums import ErrorCode
from src.core.errors.exceptions import InstanceNotFoundException
from src.core.schemas import SuccessResponse


def _to_view_model(funnel: Funnel) -> FunnelViewModel:
    return FunnelViewModel.model_validate(funnel)


class ListFunnelsUseCase:
    """Lists a bot's funnel definitions, newest first."""

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(self, bot_id: UUID) -> list[FunnelViewModel]:
        """
        Executes the business logic for listing a bot's funnels.

        Args:
            bot_id (UUID): The bot whose funnels to list.

        Returns:
            list[FunnelViewModel]: The bot's funnel definitions.
        """
        async with self.uow as uow:
            funnels = await uow.funnels.list_for_bot(uow.session, bot_id)
            return [_to_view_model(funnel) for funnel in funnels]


class GetFunnelUseCase:
    """Loads one funnel definition, scoped to its bot."""

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(self, bot_id: UUID, funnel_id: UUID) -> FunnelViewModel:
        """
        Executes the business logic for reading a single funnel.

        Args:
            bot_id (UUID): The bot the funnel must belong to.
            funnel_id (UUID): The funnel to read.

        Returns:
            FunnelViewModel: The stored definition.

        Raises:
            InstanceNotFoundException: If no such funnel exists on this bot.
        """
        async with self.uow as uow:
            funnel = await uow.funnels.get_single(
                uow.session, id=funnel_id, bot_id=bot_id
            )
            if funnel is None:
                raise InstanceNotFoundException(ErrorCode.FUNNEL_NOT_FOUND)
            return _to_view_model(funnel)


class CreateFunnelUseCase:
    """Stores a new funnel definition for a bot."""

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(self, bot_id: UUID, payload: FunnelCreate) -> FunnelViewModel:
        """
        Executes the business logic for creating a funnel.

        Args:
            bot_id (UUID): The bot to attach the funnel to.
            payload (FunnelCreate): The validated definition.

        Returns:
            FunnelViewModel: The stored definition.
        """
        async with self.uow as uow:
            funnel = await uow.funnels.create(
                uow.session,
                {
                    "bot_id": bot_id,
                    "name": payload.name,
                    "steps": payload.steps,
                    "window_seconds": payload.window_seconds,
                },
            )
            # Flush to populate the server-side defaults, then read the row
            # before committing: the commit closes the transaction the Unit of
            # Work opened, and touching the instance afterwards would emit a
            # refresh inside a context manager that is already done.
            await uow.session.flush()
            result = _to_view_model(funnel)
            await uow.commit()
            return result


class UpdateFunnelUseCase:
    """Applies a partial update to a funnel definition."""

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(
        self, bot_id: UUID, funnel_id: UUID, payload: FunnelUpdate
    ) -> FunnelViewModel:
        """
        Executes the business logic for updating a funnel.

        Args:
            bot_id (UUID): The bot the funnel must belong to.
            funnel_id (UUID): The funnel to update.
            payload (FunnelUpdate): The fields to change.

        Returns:
            FunnelViewModel: The updated definition.

        Raises:
            InstanceNotFoundException: If no such funnel exists on this bot.
        """
        changes = payload.model_dump(exclude_unset=True, exclude_none=True)

        async with self.uow as uow:
            if not changes:
                funnel = await uow.funnels.get_single(
                    uow.session, id=funnel_id, bot_id=bot_id
                )
            else:
                funnel = await uow.funnels.update(
                    uow.session, changes, id=funnel_id, bot_id=bot_id
                )
            if funnel is None:
                raise InstanceNotFoundException(ErrorCode.FUNNEL_NOT_FOUND)

            await uow.session.flush()
            result = _to_view_model(funnel)
            await uow.commit()
            return result


class DeleteFunnelUseCase:
    """Soft-deletes a funnel definition."""

    def __init__(self, uow: ApplicationUnitOfWork[RepositoryProtocol]) -> None:
        self.uow = uow

    async def execute(self, bot_id: UUID, funnel_id: UUID) -> SuccessResponse:
        """
        Executes the business logic for deleting a funnel.

        Args:
            bot_id (UUID): The bot the funnel must belong to.
            funnel_id (UUID): The funnel to delete.

        Returns:
            SuccessResponse: A success confirmation response.

        Raises:
            InstanceNotFoundException: If no such funnel exists on this bot.
        """
        async with self.uow as uow:
            funnel = await uow.funnels.delete(uow.session, id=funnel_id, bot_id=bot_id)
            if funnel is None:
                raise InstanceNotFoundException(ErrorCode.FUNNEL_NOT_FOUND)
            await uow.commit()
            return SuccessResponse(success=True)
