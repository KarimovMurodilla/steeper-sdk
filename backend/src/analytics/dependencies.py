from fastapi import Depends

from src.analytics.usecases.get_audience_metrics import GetBotAudienceMetricsUseCase
from src.analytics.usecases.get_traffic_metrics import GetBotTrafficMetricsUseCase
from src.core.database.session import get_unit_of_work
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork


def get_bot_traffic_metrics_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> GetBotTrafficMetricsUseCase:
    return GetBotTrafficMetricsUseCase(uow=uow)


def get_bot_audience_metrics_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> GetBotAudienceMetricsUseCase:
    return GetBotAudienceMetricsUseCase(uow=uow)
