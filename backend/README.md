# Steeper — Backend

Async **FastAPI** backend for the [Steeper](../README.md) Telegram bot operations
platform: register bots, ingest Telegram webhooks, run a live operator chat over
WebSockets, dispatch broadcasts, and expose metrics — all behind a modular
domain architecture with a full Docker stack.

## Key Features

- **Modular domain structure** — each domain (`bot`, `communication`,
  `marketing`, `crm`, `analytics`, `realtime`, `user`, `system`,
  `integrations/telegram`) is a self-contained package with its own routers, services, use cases, and
  repositories.
- **Async data layer** — SQLAlchemy (async) with a repository + Unit of Work
  pattern for transactional work.
- **Caching** — Redis cache layer (`src/core/redis/*`) with tags, decorators,
  and lifecycle helpers.
- **Rate limiting** — limiter package (`src/core/limiter`) exposing FastAPI
  dependencies (both IP- and user-based).
- **Background work** — Celery workers/beat on a RabbitMQ broker, with Flower
  as the monitoring UI (used for broadcasts and email).
- **Realtime** — WebSocket gateway (`src/realtime`) fanning RabbitMQ events out
  to connected operators.
- **Telegram integration** — webhook ingestion and an async Telegram Bot API
  client (`src/integrations/telegram`).
- **Auth & JWT** — operator login with password + refresh tokens and a
  permissions system (`src/user/auth`).
- **Email** — templated mailer with Celery tasks for async sending.
- **Storage** — async S3 adapter (`src/core/storage/s3`) with presigned URLs.
- **i18n** — translatable error messages (`src/core/i18n`).
- **Observability** — structured logging, retry utilities, health route,
  optional Sentry.
- **Type safety** — mypy in strict mode (no implicit Optional, no untyped
  defs, no `Any` in generics).
- **Tooling** — ruff (lint + format), mypy, pytest (asyncio), Alembic.

## API Surface

All application routes are versioned under `/v1`; system routes sit at the root.

| Tag            | Method & path                                        | Purpose |
|----------------|------------------------------------------------------|---------|
| Users          | `POST /v1/users/auth/login/password`                 | Password login (returns JWT access + refresh) |
| Users          | `POST /v1/users/auth/login/refresh`                  | Exchange a refresh token for a new access token |
| Users          | `GET  /v1/users/me`                                  | Current operator profile |
| Users          | `GET  /v1/users/{user_id}`                           | Fetch an operator by id |
| Bots           | `POST /v1/bots/`                                      | Register a bot |
| Bots           | `GET  /v1/bots/`                                      | List bots |
| Bots           | `PATCH /v1/bots/{bot_id}`                             | Update a bot |
| Bots           | `DELETE /v1/bots/{bot_id}`                            | Remove a bot |
| Communications | `POST /v1/communications/webhook/{bot_id}`           | Telegram webhook ingestion |
| Communications | `POST /v1/communications/webhook/{bot_id}/bot-message` | Record an outbound bot message |
| Chats          | `GET  /v1/bots/{bot_id}/chats`                        | List chats for a bot |
| Chats          | `GET  /v1/bots/{bot_id}/chats/{chat_id}/messages`    | List messages in a chat |
| Chats          | `POST /v1/bots/{bot_id}/chats/{chat_id}/messages`    | Operator sends a message |
| Metrics        | `GET  /v1/bots/{bot_id}/metrics/traffic`             | Update/message volume, breakdowns, heatmap |
| Metrics        | `GET  /v1/bots/{bot_id}/metrics/audience`            | Users, growth, DAU/WAU/MAU, churn, languages |
| Broadcasts     | `POST /v1/broadcasts/`                                | Create a broadcast |
| Broadcasts     | `GET  /v1/broadcasts/`                                | List broadcasts |
| Broadcasts     | `POST /v1/broadcasts/{broadcast_id}/send`            | Dispatch a broadcast (background) |
| Broadcasts     | `GET  /v1/broadcasts/{broadcast_id}/stats`           | Delivery stats |
| WebSocket      | `WS   /v1/ws`                                         | Realtime operator stream |
| System         | `GET/HEAD /health/`                                  | Health check |
| System         | `GET  /time/`                                         | Server time |

Interactive schema: `http://localhost:8000/docs` (or `http://localhost:8001/docs`
to bypass Nginx).

## Quick Start

- Install Docker and Docker Compose (Python 3.12 only needed for local
  scripts/hooks).
- Copy env: `cp .env.example .env` and fill required values. For tests you can
  also use `.env.test` (picked up when `TESTING=true` in env).
- Dev with reload: `make run-dev` (Nginx on 8000, app on 8001).
- Prod-like: `make run`.
- First run: `make migrate` then `make createsuperuser`.
- Stop: `make down`; logs: `make logs`; tests: `make test`; lint: `make lint`.

> Make targets shown here are the backend targets. From the repository root the
> top-level `Makefile` also provides full-stack targets such as
> `make run-fullstack-dev`. See the [root README](../README.md).

## Deploy your own Steeper (published images)

For self-hosting you don't have to build anything: the backend and frontend are
published to GHCR and run via a pull-only compose file
(`infra/docker-compose.prod.yml`). Postgres/Redis/RabbitMQ stay on the internal
network; only Nginx is exposed (port 8000).

Run from the repo root:

```bash
# 1. Configure environment
cp backend/.env.example backend/.env   # then edit: DB/Redis/RabbitMQ passwords,
                                        # JWT secrets, super-admin credentials, ...

# 2. Pull images and start the stack
make prod-pull
make prod-up                            # or: STEEPER_TAG=0.1.0 make prod-up

# 3. First run only — migrate the DB and create the admin user
make prod-migrate
make prod-createsuperuser

# Logs / stop
make prod-logs
make prod-down
```

Then open `http://<host>:8000` (operator panel) and `http://<host>:8000/docs`
(API). Put a TLS-terminating proxy in front of port 8000 for production.

Images (pin a release with `STEEPER_TAG`, default `latest`):
- `ghcr.io/karimovmurodilla/steeper-backend`
- `ghcr.io/karimovmurodilla/steeper-frontend`

Connect a Telegram bot with the [`steeper`](https://github.com/KarimovMurodilla/steeper)
library: add a bot in the operator panel's sidebar switcher (or via
`POST /v1/bots/`) to get its `bot_id`, then point the middleware's `base_url` at
`http://<host>:8000`.

> The frontend image talks to the API on its own origin (same-origin, behind the
> bundled Nginx). To bake a different backend URL, rebuild it with
> `--build-arg VITE_API_BASE_URL=https://api.example.com`.

## Ports

Dev stack (`infra/docker-compose.yml`). Ports marked *(env)* are host ports read
from `.env`; the values below are the `.env.example` defaults.

- Nginx: 8000, proxies to app:8001
- App direct: 8001 *(env: `APP_BACKEND_PORT`)*
- Frontend: 3000 (container port 80)
- Postgres: 5432 *(env: `POSTGRES_PORT`)*
- Redis: 6379 *(env: `REDIS_PORT`)*
- RabbitMQ: 5672 *(env: `RABBITMQ_PORT`)* (AMQP), 15672 (UI)
- Flower: 5555

In `infra/docker-compose.prod.yml` only Nginx publishes a port (8000);
everything else stays on the internal `steeper-network`.

Postgres runs from a locally built image (`infra/postgres/Dockerfile`):
PostgreSQL 18 plus a custom `postgresql.conf` and a first-boot script that
creates the `pg_stat_statements` extension.

## Common Services
- API docs: http://localhost:8000/docs (or http://localhost:8001/docs directly)
- Flower: http://localhost:5555
- Health: http://localhost:8001/health/

## Useful Make Targets
- `make run-dev` — build+up with override (reload)
- `make run` — build+up prod-like
- `make migrate` / `make migration` — apply/create Alembic revisions
- `make createsuperuser` — bootstrap the super-admin operator
- `make logs` / `make logs-app` — view logs
- `make clean` — remove containers/volumes/images/orphans
- `make lint` / `make test` — quality checks

## Quality checks
- Install dev deps: `pip install -r infra/requirements/dev.txt`
- Auto-fix and format: `make lint` (`ruff check --fix` + `ruff format`)
- Verify the way CI does: `make check-lint` (`ruff check`, `ruff format --check`, `mypy src`)
- Run the test suite: `make test`

## Documentation
- Architecture & structure: [docs/readme/architecture.md](docs/readme/architecture.md)
- Infrastructure & ops: [docs/readme/infra.md](docs/readme/infra.md)
- Contributing & CI/CD: [docs/readme/contributing.md](docs/readme/contributing.md)
