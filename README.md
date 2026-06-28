# Steeper

**Steeper** is a self-hostable platform for running and operating Telegram bots —
register multiple bots, talk to your users from a live operator panel, send
broadcasts, and track analytics. It pairs an async **FastAPI** backend with a
modern **React** operator dashboard, all wired together with a one-command
Docker stack.

> Connect your bots with the companion [`steeper`](https://github.com/KarimovMurodilla/steeper)
> Python library — point its middleware at this API and incoming Telegram
> updates flow straight into the platform.

---

## Table of Contents

- [What you get](#what-you-get)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Quick start (development)](#quick-start-development)
- [Self-host with published images](#self-host-with-published-images)
- [Connecting a Telegram bot](#connecting-a-telegram-bot)
- [Services & ports](#services--ports)
- [Common commands](#common-commands)
- [CI/CD](#cicd)
- [Documentation](#documentation)
- [License](#license)

---

## What you get

- **Bot management** — register, update, and remove multiple Telegram bots from
  one place.
- **Live operator chat** — Telegram webhooks land in the platform; operators
  reply in real time over WebSockets.
- **Broadcasts** — compose and dispatch mass messages to your audience via
  background workers.
- **Analytics** — track usage and messaging activity.
- **CRM** — customer records backing the conversations.
- **Auth** — JWT-based operator login with permissions and a super-admin
  bootstrap script.

## Architecture

This is a monorepo containing two deployable apps that ship as separate Docker
images and run together behind a single Nginx reverse proxy.

```
                          ┌─────────────────────────────┐
   Telegram  ───webhook──▶│  Nginx (:8000)              │
   (steeper lib)          │   ├── / ............ frontend (operator panel)
                          │   ├── /api ......... backend (FastAPI :8001)
   Operator browser ─────▶│   └── /ws .......... realtime (WebSockets)
                          └──────────────┬──────────────┘
                                         │
        ┌──────────────┬────────────────┼──────────────┬──────────────┐
     Postgres        Redis           RabbitMQ        Celery          Flower
   (PostGIS)      (cache/limiter)    (broker)    (worker + beat)   (monitoring)
```

- **`backend/`** — async FastAPI app with a modular domain structure
  (`bot`, `communication`, `marketing`, `crm`, `analytics`, `realtime`,
  `user`, `integrations/telegram`). Uses SQLAlchemy (async) with a Unit of Work
  pattern, Redis caching/rate-limiting, Celery + RabbitMQ for background work,
  and an async S3 storage adapter.
- **`frontend/`** — React 19 + Vite + TypeScript operator panel
  (TanStack Query, Zustand, Tailwind, React Router). Pages: **Bots**, **Chats**,
  **Broadcasts**, **Analytics**, and **Login**.

## Tech stack

| Layer        | Technologies |
|--------------|--------------|
| Backend      | FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| Frontend     | React 19, Vite 6, TypeScript, TanStack Query, Zustand, Tailwind CSS |
| Data         | PostgreSQL (PostGIS), Redis |
| Async / jobs | Celery, RabbitMQ, Flower |
| Edge         | Nginx (reverse proxy + WebSocket upgrade) |
| Storage      | S3-compatible object storage (presigned URLs) |
| Tooling      | Docker Compose, Make, Ruff, mypy, pytest, pre-commit |

## Repository layout

```
steeper/
├── backend/          # FastAPI application (see backend/README.md)
│   ├── src/          # Modular domain code (bot, communication, marketing, ...)
│   ├── migrations/   # Alembic migrations
│   ├── tests/        # pytest suite
│   ├── infra/        # Dockerfiles, compose files, nginx, postgres, redis
│   └── docs/readme/  # Architecture, infra, and contributing docs
├── frontend/         # React + Vite operator panel
│   └── src/          # pages, components, api, store, hooks, types
├── .github/workflows # CI: publish images to GHCR
└── Makefile          # Top-level dev & prod orchestration
```

> The full backend layout and architectural patterns (Unit of Work, UseCase vs
> Service, repositories) are documented in
> [`backend/docs/readme/architecture.md`](backend/docs/readme/architecture.md).

## Quick start (development)

**Prerequisites:** Docker + Docker Compose. (Python 3.12 only needed if you run
backend scripts/hooks locally.)

```bash
# 1. Configure the backend environment
cp backend/.env.example backend/.env   # fill DB/Redis/RabbitMQ passwords,
                                        # JWT secrets, super-admin credentials, ...

# 2. Bring up the full stack (backend + frontend + infra) with hot-reload
make run-fullstack-dev

# 3. First run only — migrate the DB and create the admin user
make migrate
make createsuperuser
```

Then open:

- **Operator panel:** http://localhost:8000
- **API docs (Swagger):** http://localhost:8000/docs
- **Flower (task monitor):** http://localhost:5555

To run only the backend in dev mode, use `make run-dev`. Stop everything with
`make down`; view logs with `make logs`.

## Self-host with published images

You don't have to build anything — backend and frontend images are published to
GHCR and run via a pull-only compose file
(`backend/infra/docker-compose.prod.yml`). Postgres / Redis / RabbitMQ stay on
the internal network; only Nginx is exposed on port 8000.

```bash
# 1. Configure environment
cp backend/.env.example backend/.env   # edit credentials, secrets, admin user

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

Open `http://<host>:8000` (operator panel) and `http://<host>:8000/docs` (API).
**Put a TLS-terminating proxy in front of port 8000 for production.**

Images (pin a release with `STEEPER_TAG`, default `latest`):

- `ghcr.io/karimovmurodilla/steeper-backend`
- `ghcr.io/karimovmurodilla/steeper-frontend`

> The frontend image talks to the API on its own origin (same-origin, behind the
> bundled Nginx). To bake a different backend URL, rebuild it with
> `--build-arg VITE_API_BASE_URL=https://api.example.com`.

## Connecting a Telegram bot

1. Register a bot in the operator panel (or via the API) to obtain its `bot_id`.
2. In your bot built with the [`steeper`](https://github.com/KarimovMurodilla/steeper)
   library, point the middleware's `base_url` at `http://<host>:8000`.
3. Incoming Telegram updates are forwarded to the platform's webhook endpoint,
   appear in **Chats**, and operators can reply in real time.

## Services & ports

| Service   | Port           | Notes                          |
|-----------|----------------|--------------------------------|
| Nginx     | 8000           | Public entrypoint → app:8001   |
| App       | 8001           | FastAPI (direct, bypass Nginx) |
| Postgres  | 5432           | PostGIS                        |
| Redis     | 6379           | Cache / rate limiter           |
| RabbitMQ  | 5672 / 15672   | AMQP / management UI           |
| Flower    | 5555           | Celery monitoring              |

## Common commands

Run from the repo root (`make info` prints a summary):

| Command                     | Description |
|-----------------------------|-------------|
| `make run-fullstack-dev`    | Build + start backend, frontend, and infra with hot-reload |
| `make run-fullstack`        | Build + start the full stack (prod-like) |
| `make run-dev` / `make run` | Backend only (dev with reload / prod-like) |
| `make migrate`              | Apply Alembic migrations (`alembic upgrade head`) |
| `make migration`            | Create a new Alembic revision |
| `make createsuperuser`      | Create the admin user |
| `make logs` / `make logs-app` | Tail all services / just the app |
| `make test`                 | Run the backend test suite (pytest) |
| `make lint`                 | Run pre-commit hooks (ruff, mypy, ...) |
| `make down` / `make clean`  | Stop the stack / remove containers, volumes, images |
| `make prod-*`               | Pull-only production stack on published images |

## CI/CD

`.github/workflows/docker-publish.yml` builds and pushes backend and frontend
images to GHCR using the built-in `GITHUB_TOKEN` (no secrets to configure):

- Push a `vX.Y.Z` tag → publishes `X.Y.Z`, `X.Y`, and `latest` (release images).
- Push to `main` → publishes `main` and `sha-<short>` (rolling images).

## Documentation

- **Backend overview:** [`backend/README.md`](backend/README.md)
- **Architecture & structure:** [`backend/docs/readme/architecture.md`](backend/docs/readme/architecture.md)
- **Infrastructure & operations:** [`backend/docs/readme/infra.md`](backend/docs/readme/infra.md)
- **Contributing & CI/CD:** [`backend/docs/readme/contributing.md`](backend/docs/readme/contributing.md)

## License

Released under the [MIT License](LICENSE). © 2026 KarimovMurodilla.
