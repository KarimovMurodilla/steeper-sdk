from typing import Any
from uuid import UUID

from loggers import get_logger
from src.core.database.uow import ApplicationUnitOfWork, RepositoryProtocol
from src.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    make_paginated_response,
)
from src.marketing.enums import BroadcastStatus
from src.marketing.schemas import BroadcastListItem

logger = get_logger(__name__)


class ListBroadcastsUseCase:
    """Use case for listing the current user's broadcast campaigns."""

    def __init__(
        self,
        uow: ApplicationUnitOfWork[RepositoryProtocol],
    ) -> None:
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        pagination: PaginationParams,
        bot_id: UUID | None = None,
        status: BroadcastStatus | None = None,
    ) -> PaginatedResponse[BroadcastListItem]:
        """
        Returns a paginated list of broadcasts created by the given user,
        optionally filtered by bot and status.
        """
        filters: dict[str, Any] = {"created_by": user_id}
        if bot_id is not None:
            filters["bot_id"] = bot_id
        if status is not None:
            filters["status"] = status

        async with self.uow as uow:
            broadcasts, total = await uow.broadcasts.get_paginated_list(
                uow.session,
                page=pagination.page,
                size=pagination.size,
                **filters,
            )

        return make_paginated_response(
            items=broadcasts,
            total=total,
            pagination=pagination,
            schema=BroadcastListItem,
        )
