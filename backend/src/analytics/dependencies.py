from fastapi import Depends

from src.analytics.usecases.get_bot_summary import GetBotAnalyticsSummaryUseCase
from src.analytics.usecases.get_update_stats import GetBotUpdateStatsUseCase
from src.core.database.session import get_unit_of_work
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork


def get_bot_analytics_summary_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> GetBotAnalyticsSummaryUseCase:
    return GetBotAnalyticsSummaryUseCase(uow=uow)


def get_bot_update_stats_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> GetBotUpdateStatsUseCase:
    return GetBotUpdateStatsUseCase(uow=uow)
