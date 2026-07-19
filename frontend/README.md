# Steeper — Frontend

Operator dashboard for the [Steeper](../README.md) platform: a **React 19 + Vite
+ TypeScript** single-page app where operators manage bots, chat with users in
real time, run broadcasts, and view analytics.

## Tech stack

| Concern        | Library |
|----------------|---------|
| Framework      | React 19, Vite 6, TypeScript |
| Data fetching  | TanStack Query (`@tanstack/react-query`) |
| Client state   | Zustand (`authStore`, `uiStore`) |
| Routing        | React Router (`react-router-dom` v7) |
| HTTP           | Axios (with a shared client + token-refresh interceptor) |
| Styling        | Tailwind CSS |
| Icons / toasts | lucide-react, react-hot-toast |

## Routes

Routing lives in `src/App.tsx`. All app routes render inside `AppLayout`
(sidebar + auth guard); `/login` and the 404 page render standalone.

| Path          | Page              | Notes |
|---------------|-------------------|-------|
| `/login`      | `LoginPage`       | Password login |
| `/`           | →                 | Redirects to `/chats` |
| `/chats`      | `ChatPage`        | Live operator chat (WebSocket) |
| `/broadcasts` | `BroadcastsPage`  | Create/list broadcasts, view stats |
| `/analytics`  | `AnalyticsPage`   | Per-bot metrics and charts |
| `*`           | `NotFoundPage`    | Fallback |

## Project layout

```
src/
├── api/          # Axios client + per-domain API modules (auth, bots, chats,
│                 #   broadcasts, analytics)
├── components/   # Feature components (Bot, Chat, Broadcast, Analytics, Layout)
│   └── ui/       # Reusable primitives (Button, Modal, Input, Avatar, ...)
├── hooks/        # TanStack Query hooks + useWebSocket, useActiveBot
├── pages/        # Route-level pages
├── store/        # Zustand stores (auth, UI)
├── types/        # Shared API and WebSocket types
├── lib/          # Small utilities
├── App.tsx       # Router + providers
└── main.tsx      # Entry point
```

## Development

The app expects the Steeper backend to be reachable. In dev, Vite proxies `/v1`
and `/health` to the backend (default target `http://app:8001`, overridable with
`VITE_API_PROXY_TARGET`), so no CORS setup is needed.

```bash
npm install
npm run dev        # Vite dev server on http://localhost:5173
```

The simplest path is to run the whole stack from the repo root with
`make run-fullstack-dev`, which serves the frontend behind Nginx on port 8000
alongside the backend and infra.

### Scripts

| Command           | Description |
|-------------------|-------------|
| `npm run dev`     | Start the Vite dev server (port 5173) |
| `npm run build`   | Type-check (`tsc -b`) and build for production |
| `npm run preview` | Preview the production build locally |
| `npm run lint`    | Run ESLint |

## Configuration

Vite bakes `VITE_*` variables at **build time**:

| Variable            | Default | Purpose |
|---------------------|---------|---------|
| `VITE_API_BASE_URL` | `""` (same-origin) | Base URL for API requests. Empty means "talk to the API on the same origin", which is correct behind the bundled Nginx. |
| `VITE_WS_HOST`      | `""`    | Optional explicit host for the WebSocket connection. |

The `axios` client sends the stored access token on every request and
transparently refreshes it on `401` (and on a WebSocket `1008` close), so
operators are not logged out when a token expires.

## Docker

The production image is a multi-stage build (Node → Nginx) published to GHCR as
`ghcr.io/karimovmurodilla/steeper-frontend`. To bake a non-same-origin backend
URL into the bundle:

```bash
docker build \
  --build-arg VITE_API_BASE_URL=https://api.example.com \
  -t steeper-frontend ./frontend
```

See the [root README](../README.md) for the full self-hosting flow.
</content>
