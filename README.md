# Steeper

**Steeper** is a self-hostable platform for running and operating Telegram bots. Register
multiple bots, talk to your users from a live operator panel, send broadcasts, and track
metrics. An async FastAPI backend and a React operator dashboard, wired together with a
one-command Docker stack.

> Connect your bots with the companion [`steeper`](https://github.com/KarimovMurodilla/steeper)
> Python library — point its middleware at this API and incoming Telegram updates flow
> straight into the platform.

## What you get

- **Bot management** — register, update, and remove multiple Telegram bots.
- **Live operator chat** — Telegram webhooks land in the platform; operators reply in real
  time over WebSockets.
- **Broadcasts** — compose and dispatch mass messages to your audience.
- **Metrics** — update and message volume, content and chat breakdowns, an activity
  heatmap, growth, DAU/WAU/MAU, churn, and languages.
- **Bot logs** — bots ship their `logging` output to the platform; read the live stream and
  search the history.
- **Audience records** — every Telegram user who talks to a bot is stored and reused for
  chat identity, broadcast targeting, and metrics.
- **Auth** — JWT-based operator login with permissions and a super-admin bootstrap script.

## Quick start (development)

**Prerequisites:** Docker + Docker Compose.

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

To run only the backend in dev mode, use `make run-dev`. Stop everything with `make down`;
view logs with `make logs`.

## Self-host with published images

Backend and frontend images are published to GHCR, so nothing has to be built by hand:

- `ghcr.io/karimovmurodilla/steeper-backend`
- `ghcr.io/karimovmurodilla/steeper-frontend`

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

`STEEPER_TAG` selects the version, default `latest` (a rolling tag following `main`). To pin
a release, set it in **both** `make prod-pull` and `make prod-up` — pulling with one tag and
starting with another leaves the old image running.

## Connecting a Telegram bot

1. Add a bot in the operator panel's sidebar switcher (**Add Bot** → paste the @BotFather
   token), or via the API. Click its ID in the switcher to copy the `bot_id`.
2. In your bot built with the [`steeper`](https://github.com/KarimovMurodilla/steeper)
   library, point the middleware's `base_url` at `http://<host>:8000`.
3. Incoming Telegram updates are forwarded to the platform's webhook endpoint, appear in
   **Chats**, and operators can reply in real time.

## Common commands

Run from the repo root; `make info` prints the full list.

| Command                  | Description |
|--------------------------|-------------|
| `make run-fullstack-dev` | Build + start backend, frontend, and infra with hot-reload |
| `make run-dev`           | Backend only, with reload |
| `make migrate`           | Apply Alembic migrations |
| `make createsuperuser`   | Create the admin user |
| `make test`              | Run the backend test suite (pytest) |
| `make lint`              | Auto-fix lint errors and format the backend |
| `make down`              | Stop the stack |

## Documentation

- **Backend overview:** [`backend/README.md`](backend/README.md)
- **Architecture & structure:** [`backend/docs/readme/architecture.md`](backend/docs/readme/architecture.md)
- **Infrastructure & operations:** [`backend/docs/readme/infra.md`](backend/docs/readme/infra.md)
- **Contributing & CI/CD:** [`backend/docs/readme/contributing.md`](backend/docs/readme/contributing.md)

## License

Released under the [MIT License](LICENSE). © 2026 KarimovMurodilla.
