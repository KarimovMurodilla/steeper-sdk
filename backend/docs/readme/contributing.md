# Contributing and CI/CD

## How to Contribute
1. Fork and branch: `git checkout -b feature/your-feature`.
2. Follow the project's typing and lint rules (mypy strict, ruff, black).
3. Run checks locally: `make lint` and `make test`.
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

### Publish images (`.github/workflows/docker-publish.yml`)
The single workflow builds and pushes the backend and frontend images to GHCR
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
</content>
