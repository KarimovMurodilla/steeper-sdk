# Infrastructure and Operations

## Services and Ports

Dev stack (`infra/docker-compose.yml`). Ports marked *(env)* are host ports read
from `.env`; the values below are the `.env.example` defaults.

- Nginx: 8000 (proxies to app)
- App: 8001 (FastAPI) *(env: `APP_BACKEND_PORT`)*
- Frontend: 3000 (container port 80)
- Postgres: 5432 *(env: `POSTGRES_PORT`)*
- Redis: 6379 *(env: `REDIS_PORT`)*
- RabbitMQ: 5672 *(env: `RABBITMQ_PORT`)* (AMQP), 15672 (UI)
- Flower: 5555

Configs live in `infra/` (compose, nginx, dockerfiles, redis/postgres, requirements).

## Compose files
- `docker-compose.yml` — base dev/prod-like stack, builds images from the repo.
- `docker-compose.override.yml` — dev overrides (hot-reload), applied by `make run-dev`.
- `docker-compose.prod.yml` — pull-only stack on published GHCR images. Only
  Nginx publishes a host port (8000); Postgres/Redis/RabbitMQ/app/Flower stay on
  the internal `steeper-network`. Postgres is still built locally
  (`make prod-build-db`), since its image is infra rather than a published app image.

## Containers
- **Postgres:** built from `infra/postgres/Dockerfile` — PostgreSQL 18 with a
  custom `postgresql.conf` and a first-boot script creating the
  `pg_stat_statements` extension. Data lives in the `app-postgres-data-steeper` volume.
- **Frontend:** React build served by its own Nginx, proxied at `/`.
- **App:** Uvicorn/Gunicorn serving FastAPI.
- **Celery_worker:** Background tasks.
- **Celery_beat:** Schedules periodic tasks.
- **Flower:** Celery monitoring UI.
- **Nginx:** Reverse proxy to app.
- **Redis:** Cache/result backend with password.
- **RabbitMQ:** Broker with management UI.

## Prerequisites
- Python 3.12 (for local scripts/hooks)
- Docker
- Docker Compose

## Quick Start
```bash
cp .env.example .env   # main env
cp .env.test .env.test # optional test env (used when TESTING=true)
make run-dev          # dev images + autoreload, exposes 8000 via nginx
# or:
make run              # prod-like build
```

Open:
- App via Nginx: http://localhost:8000
- Docs: http://localhost:8000/docs
- Direct app (bypass Nginx): http://localhost:8001/docs
- Flower: http://localhost:5555

These targets bring up the backend only. To run backend + frontend together, use
the root `Makefile`: `make run-fullstack-dev` (hot-reload) or `make run-fullstack`.
For the published-images stack: `make prod-pull && make prod-up`.

Nginx routing (`infra/nginx/app.conf`): `/v1` → app (API and WebSockets),
`/docs`, `/openapi.json`, `/health` → app, everything else → frontend.

## Common Commands
```bash
make run-dev          # build+up with override (reload)
make run              # build+up prod-like
make logs             # tail all services
make logs-app         # app logs
make migrate          # alembic upgrade head
make migration        # create alembic revision
make test             # pytest
make lint             # ruff auto-fix + format
make check-lint       # ruff + mypy, same as CI
make down             # stop stack
make clean            # remove stack + volumes/images/orphans
```

## Troubleshooting
- Ensure Docker/Compose are installed.
- `.env` must be filled (ports, DB/Redis/RabbitMQ credentials). `.env.test` used for local test runs `make test`.
- Use `make logs` or service-specific logs to inspect errors.
- If migrations fail, check Postgres health first.
