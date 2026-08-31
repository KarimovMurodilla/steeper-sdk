"""Bot-logs subdomain dependencies."""

from fastapi import Depends

from src.core.database.session import get_unit_of_work
from src.core.database.uow.abstract import RepositoryProtocol
from src.core.database.uow.application import ApplicationUnitOfWork
from src.main.config import config
from src.system.logs.loki import LokiClient
from src.system.logs.usecases.ingest_logs import IngestBotLogsUseCase
from src.system.logs.usecases.list_logs import ListBotLogsUseCase

# One client (and one connection pool) for the process: ingestion is the hot
# path of this feature, and a per-request client would dominate its cost.
_loki_client = LokiClient(
    base_url=config.loki.LOKI_URL,
    timeout=config.loki.LOKI_TIMEOUT,
    max_limit=config.loki.LOKI_QUERY_MAX_LIMIT,
)


def get_loki_client() -> LokiClient:
    """Return the singleton LokiClient instance."""
    return _loki_client


def get_ingest_bot_logs_use_case(
    uow: ApplicationUnitOfWork[RepositoryProtocol] = Depends(get_unit_of_work),
    loki: LokiClient = Depends(get_loki_client),
) -> IngestBotLogsUseCase:
    return IngestBotLogsUseCase(uow=uow, loki=loki)


def get_list_bot_logs_use_case(
    loki: LokiClient = Depends(get_loki_client),
) -> ListBotLogsUseCase:
    return ListBotLogsUseCase(loki=loki)
