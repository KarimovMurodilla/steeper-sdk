# Contributing and CI/CD

## How to Contribute
1. Fork and branch: `git checkout -b feature/your-feature`.
2. Follow the project's typing and lint rules (mypy strict, ruff).
3. Run checks locally: `make check-lint` and `make test`.
4. Commit and open a PR with a clear description.

### Coding conventions
Module-level conventions are captured as short rules under
[`backend/.agents/rules/`](../../.agents/rules/) and are worth reading before a
first contribution:
- Keep router bodies thin — delegate to use cases.
- Always use the Unit of Work inside use cases.
- Implement schemas in `schemas.py` and DI factories in `dependencies.py`.
- Import modules at the top of the file; don't create redundant use cases.

## CI/CD (GitHub Actions)

Both workflows live in the repository root under `.github/workflows/` — GitHub
only reads that top-level directory, so workflow files nested inside `backend/`
would silently never run.

### Checks (`.github/workflows/ci.yml`)
Runs on every push and pull request against `main`, in two parallel jobs:

- **Backend** — `ruff check`, `ruff format --check`, `mypy src`, a single-head
  Alembic guard, and `pytest`. Both `.env` and `.env.test` are generated from
  `backend/.env.example`, since settings are validated at import time.
- **Frontend** — `npm ci`, `npm run lint`, `npm run build`.

`make check-lint` and `make test` run the backend half locally.

### Publish images (`.github/workflows/docker-publish.yml`)
This workflow builds and pushes the backend and frontend images to GHCR
using the built-in `GITHUB_TOKEN` (no secrets to configure):

- Push a `vX.Y.Z` tag → publishes `X.Y.Z`, `X.Y`, and `latest` (release images).
- Push to `main` → publishes `main` and `sha-<short>` (rolling images).

Published images:
- `ghcr.io/karimovmurodilla/steeper-backend`
- `ghcr.io/karimovmurodilla/steeper-frontend`

### Deploying published images
Deployment is pull-only via `infra/docker-compose.prod.yml` and the `prod-*`
Make targets — see [infra.md](infra.md) and the
[backend README](../../README.md#deploy-your-own-steeper-published-images).
