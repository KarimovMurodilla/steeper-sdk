from fastapi import Depends

from src.analytics.usecases.get_audience_metrics import GetBotAudienceMetricsUseCase
from src.analytics.usecases.get_funnel_report import GetFunnelReportUseCase
from src.analytics.usecases.get_traffic_metrics import GetBotTrafficMetricsUseCase
from src.analytics.usecases.ingest_events import IngestBotEventsUseCase
from src.analytics.usecases.list_event_names import ListEventNamesUseCase
from src.analytics.usecases.manage_funnels import (
    CreateFunnelUseCase,
    DeleteFunnelUseCase,
    GetFunnelUseCase,
    ListFunnelsUseCase,
    UpdateFunnelUseCase,
)
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


def get_ingest_bot_events_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> IngestBotEventsUseCase:
    return IngestBotEventsUseCase(uow=uow)


def get_list_event_names_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> ListEventNamesUseCase:
    return ListEventNamesUseCase(uow=uow)


def get_list_funnels_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> ListFunnelsUseCase:
    return ListFunnelsUseCase(uow=uow)


def get_funnel_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> GetFunnelUseCase:
    return GetFunnelUseCase(uow=uow)


def get_create_funnel_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> CreateFunnelUseCase:
    return CreateFunnelUseCase(uow=uow)


def get_update_funnel_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> UpdateFunnelUseCase:
    return UpdateFunnelUseCase(uow=uow)


def get_delete_funnel_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> DeleteFunnelUseCase:
    return DeleteFunnelUseCase(uow=uow)


def get_funnel_report_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
) -> GetFunnelReportUseCase:
    return GetFunnelReportUseCase(uow=uow)
