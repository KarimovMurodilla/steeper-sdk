# Architecture and Structure

## Core Architectural Patterns

### Unit of Work (UoW) Pattern
`src/core/database/uow.py` keeps DB work transactional and coordinates repositories.

- Transaction management: groups multiple DB operations to succeed or fail together.
- Repository coordination: single transaction boundary for multiple repositories.
- Clean API design: consistent interface (`commit`, `rollback`) for callers.

Implementations:
- `AbstractUnitOfWork`: contract.
- `SQLAlchemyUnitOfWork`: AsyncSession-based implementation.
- `ApplicationUnitOfWork`: app-specific factory wiring repositories.

### Main Module Architecture
`src/main/` wires the app and isolates bootstrapping concerns.
- `config.py`: Pydantic settings for DB, Redis, RabbitMQ, JWT, etc. `.env` is used by default; `.env.test` is used when `TESTING=true`. `SENTRY_ENABLED` gates Sentry even if DSN is set; Sentry is skipped in DEBUG/TESTING.
- `lifespan.py`: startup/shutdown lifecycle (init/cleanup external resources).
- `presentation.py`: API assembly, versioning, exception handlers.
- `route_logging.py`: logs routes grouped by method/tag for debugging.
- `web.py`: FastAPI app factory with middleware, CORS, Sentry, routers.

Benefits:
- Separation of concerns per file.
- Modularity and extendability.
- Centralized configuration and consistent error handling.
- Clear startup/shutdown ownership for resources.

### Core Components (extended)
- **Storage (S3):** Async adapter in `src/core/storage/s3` with presigned URLs, UploadFile support, and paginated listings. Use via DI (`src/core/storage/s3/dependencies.get_s3_adapter`).

### UseCase vs Service (Formalization)
**UseCase (Application Service)**
- Use when the operation is a scenario, not a single business rule.
- Always: controls the transaction (UoW), orchestrates steps, may touch multiple repositories/services, may call external ports (S3/Email/Payment/HTTP), is responsible for side effects (events/queues), and shapes the final DTO/response.
- Forbidden: heavy business logic inside; push domain rules into Services.

**Service (Domain / Module Service)**
- Encapsulates business logic of a single module.
- By default: uses only its own repository, no external systems, no cross-context knowledge, holds domain rules (validations/invariants/calculations).
- Exceptions: may use multiple repositories of the same bounded context if it stays a pure domain rule (not a scenario or I/O process).
- Size rule of thumb: if a method grows beyond ~30–40 LOC, has 3+ branches, or 3+ sequential steps, it’s turning into a scenario → move to a UseCase.

**External systems (S3, Email, Queues, HTTP clients)**
- Always at the UseCase level or in infra adapters used by a UseCase.

### Repository Access
- All DB work goes through repositories; no direct SQL in usecases/services/routers.
- Prefer base repository methods (e.g., `get_single`) before adding custom queries; if the same filters/settings are reused 2–3 times or more, extract them into a custom repository method.
- Keep repositories focused on data access; put orchestration and business logic in usecases/services.

### Module Anatomy
Each domain module is a self-contained package. A typical module contains:
- `routers.py` — thin FastAPI routes (delegate to use cases, no business logic).
- `schemas.py` — Pydantic request/response models.
- `models.py` — SQLAlchemy ORM models.
- `repositories/` (or `repositories.py`) — data access.
- `services/` — single-module domain rules.
- `usecases/` — scenario orchestration across repositories/services and external ports.
- `dependencies.py` — DI factories wiring services/use cases.
- `tasks.py` — Celery tasks owned by the module (where applicable).

---
## Domain Modules
The application is split into the following domains, all registered under the
`/v1` prefix in `src/main/presentation.py` (system routes sit at the root):

- **`user/`** — operators and authentication. `auth/` holds JWT password login,
  refresh tokens (see `auth/REFRESH_TOKEN_IMPLEMENTATION.md`), and a permissions
  system. Endpoints: login, refresh, current user, get user by id.
- **`bot/`** — registry of Telegram bots (`Bot` model). CRUD endpoints:
  create, list, update, delete.
- **`communication/`** — Telegram ingestion. Webhook endpoints persist raw
  `TelegramUpdate`s and derive `Chat`, `Message`, and `TelegramUser` records.
  The `chat/` subpackage backs the operator chat (list chats, list messages,
  send a message).
- **`marketing/`** — broadcasts. Create/list broadcasts, dispatch them via
  background workers, and read delivery stats (`Broadcast`, `BroadcastDelivery`).
- **`analytics/`** — per-bot aggregate metrics and update-volume time series.
- **`crm/`** — customer records (`TelegramUser`) backing conversations.
- **`realtime/`** — WebSocket gateway (`/v1/ws`). Each gateway instance binds an
  exclusive RabbitMQ queue and fans platform events out to connected operators.
- **`integrations/telegram/`** — async Telegram Bot API client used to send
  outbound messages and manage bots.
- **`system/`** — infrastructure routes: health check and server time.

---
## Project Layout
```
├── infra/                               # Infrastructure and deployment assets
│   ├── docker/                          # Docker configuration files
│   │   ├── Dockerfile                   # Production Dockerfile (multi-stage build)
│   │   └── Dockerfile.dev               # Development Dockerfile with hot-reload
│   ├── docker-compose.override.yml      # Docker Compose overrides for development
│   ├── docker-compose.yml               # Docker Compose configuration
│   ├── nginx/                           # Nginx configuration
│   │   ├── app.conf                     # App reverse-proxy config
│   │   ├── main.conf                    # Shared proxy settings (upgrade headers, etc.)
│   │   └── dev-nginx.conf               # Dev-only reverse-proxy config
│   ├── postgres/                        # PostgreSQL configuration
│   │   ├── Dockerfile-postgis           # Dockerfile for PostgreSQL with PostGIS
│   │   ├── init-postgis.sh              # Initialization script
│   │   └── postgresql.conf              # PostgreSQL configuration
│   ├── redis.conf                       # Redis configuration
│   ├── requirements/                    # Python dependencies for different environments
│   │   ├── base.txt                     # Base dependencies used in all environments
│   │   ├── dev.txt                      # Development environment dependencies
│   │   └── prod.txt                     # Production environment dependencies
│   └── requirements.txt                 # Main requirements file
│
├── migrations/                          # Alembic migrations for database schema management
│   ├── versions/                        # Migration version files
│   ├── env.py                           # Alembic environment configuration
│   ├── script.py.mako                   # Alembic migration script template
│   └── README                           # Instructions for migrations
│
├── scripts/                             # Utility scripts for the application
│   ├── __init__.py                      # Package initialization
│   └── check_env.py                     # Environment validation script
│
├── src/                                 # Application source code
│   ├── core/                            # Core components shared across the application
│   │   ├── database/                    # Database connection and ORM setup
│   │   ├── email_service/               # Email service functionality
│   │   ├── errors/                      # Exceptions and handlers
│   │   ├── i18n/                         # Translatable error messages
│   │   ├── limiter/                     # Rate limiting functionality
│   │   ├── pagination/                  # Pagination helpers
│   │   ├── patterns/                    # Shared design patterns
│   │   ├── redis/                       # Redis caching system + limiter init
│   │   ├── storage/                     # Storage adapters (S3)
│   │   ├── utils/                       # Utility functions
│   │   ├── middleware.py                # Application middleware setup
│   │   ├── schemas.py                   # Core data validation schemas
│   │   ├── services.py                  # Core services shared across modules
│   │   └── validations.py               # Data validation utilities
│   │
│   ├── main/                            # Application entry points
│   │   ├── config.py                    # Application configuration settings
│   │   ├── lifespan.py                  # Application lifecycle management
│   │   ├── presentation.py              # API presentation layer
│   │   ├── route_logging.py             # Utility for logging routes summary
│   │   └── web.py                       # FastAPI application setup
│   │
│   ├── user/                            # Operators, auth (JWT + refresh), permissions
│   │   ├── auth/                        # Login, refresh tokens, permissions
│   │   ├── dependencies.py              # DI factories
│   │   ├── models.py                    # ORM models
│   │   ├── repositories.py              # Data access
│   │   ├── routers.py                   # API endpoints
│   │   ├── schemas.py                   # Pydantic schemas
│   │   ├── services.py                  # Domain services
│   │   ├── tasks.py                     # Celery tasks
│   │   └── usecases/                    # Use cases
│   │
│   ├── bot/                             # Telegram bot registry (CRUD)
│   ├── communication/                   # Webhook ingestion + operator chat (chat/)
│   ├── marketing/                       # Broadcasts and delivery tracking
│   ├── analytics/                       # Per-bot analytics endpoints
│   ├── crm/                             # Customer (Telegram user) records
│   ├── realtime/                        # WebSocket gateway + RabbitMQ consumers
│   ├── integrations/                    # External integrations
│   │   └── telegram/                    # Async Telegram Bot API client
│   └── system/                          # Health and time routes
│
├── tests/                               # Test suite
│   ├── auth/                            # Auth tests
│   ├── core/                            # Core tests
│   ├── email/                           # Email tests
│   ├── main/                            # Main module tests
│   ├── storage/                         # Storage adapter tests
│   └── system/                          # System routes tests
│
├── celery_tasks/                        # Celery task management
├── loggers/                             # Logging configurations
├── models/                              # Shared data models and models package initialization
├── Makefile                             # Makefile with predefined commands
├── alembic.ini                          # Alembic configuration file
├── pytest.ini                           # PyTest configuration
├── mypy.ini                             # MyPy configuration
├── README.md                            # Project documentation
└── pyproject.toml                       # Project and tooling configuration
```
