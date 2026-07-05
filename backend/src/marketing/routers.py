from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.pagination import PaginatedResponse, PaginationParams
from src.core.schemas import SuccessResponse
from src.marketing.dependencies import (
    get_create_broadcast_use_case,
    get_get_broadcast_stats_use_case,
    get_launch_broadcast_use_case,
    get_list_broadcasts_use_case,
)
from src.marketing.enums import BroadcastStatus
from src.marketing.schemas import (
    BroadcastCreateRequest,
    BroadcastListItem,
    BroadcastResponse,
    BroadcastStatsResponse,
)
from src.marketing.usecases.create_campaign import CreateBroadcastUseCase
from src.marketing.usecases.get_campaign_stats import GetBroadcastStatsUseCase
from src.marketing.usecases.launch_broadcast import LaunchBroadcastUseCase
from src.marketing.usecases.list_broadcasts import ListBroadcastsUseCase
from src.user.auth.dependencies import get_current_user
from src.user.models import User

router = APIRouter()


@router.post(
    "/",
    response_model=BroadcastResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid payload format"},
        403: {"description": "Permission denied"},
    },
)
async def create_broadcast(
    data: BroadcastCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[CreateBroadcastUseCase, Depends(get_create_broadcast_use_case)],
) -> BroadcastResponse:
    """
    Creates a new broadcast campaign.
    If schedule_at is provided, the broadcast will be scheduled for that time.
    """
    return await use_case.execute(user_id=current_user.id, data=data)


@router.get(
    "/",
    response_model=PaginatedResponse[BroadcastListItem],
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
    },
)
async def list_broadcasts(
    pagination: Annotated[PaginationParams, Depends()],
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[ListBroadcastsUseCase, Depends(get_list_broadcasts_use_case)],
    bot_id: UUID | None = None,
    status_filter: Annotated[BroadcastStatus | None, Query(alias="status")] = None,
) -> PaginatedResponse[BroadcastListItem]:
    """
    Returns a paginated list of broadcasts created by the current user,
    optionally filtered by bot and status.
    """
    return await use_case.execute(
        user_id=current_user.id,
        pagination=pagination,
        bot_id=bot_id,
        status=status_filter,
    )


@router.post(
    "/{broadcast_id}/send",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Broadcast not found"},
        409: {"description": "Broadcast not in a sendable state"},
    },
)
async def send_broadcast(
    broadcast_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[LaunchBroadcastUseCase, Depends(get_launch_broadcast_use_case)],
) -> SuccessResponse:
    """
    Launches a broadcast campaign. Dispatches a Celery task for processing.
    """
    return await use_case.execute(broadcast_id=broadcast_id)


@router.get(
    "/{broadcast_id}/stats",
    response_model=BroadcastStatsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Permission denied"},
        404: {"description": "Broadcast not found"},
    },
)
async def get_broadcast_stats(
    broadcast_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[
        GetBroadcastStatsUseCase, Depends(get_get_broadcast_stats_use_case)
    ],
) -> BroadcastStatsResponse:
    """
    Returns delivery statistics for a broadcast campaign.
    """
    return await use_case.execute(broadcast_id=broadcast_id)
