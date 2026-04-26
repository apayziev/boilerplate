# CLAUDE.md

Guidance for Claude Code (and other AI coding assistants) working in this repository. Keep this file accurate — a stale CLAUDE.md misleads the assistant.

## Stack at a glance

- **Backend:** FastAPI + SQLAlchemy 2.0 (async, asyncpg) + PostgreSQL + Redis (ARQ queue, rate limiting). Python 3.11+.
- **Frontend:** React 19 + Vite + TanStack Router (file-based) + TanStack Query + Tailwind v4 + Radix + shadcn-style components + next-themes.
- **Auth:** JWT cookies (httpOnly, samesite=strict). Login accepts **username OR Uzbekistan E.164 phone (`+998…`)**. No email, by design.
- **Edge:** Caddy in prod (`{$SITE_ADDRESS::80}` env-templated, auto-HTTPS when a domain is set). Local dev uses port-exposed services without a proxy.
- **Codegen:** Frontend TS client auto-generated from the backend OpenAPI spec.
- **CI:** GitHub Actions runs ruff + mypy. Pytest and Playwright are kept on disk and run locally — `test`/`frontend-e2e` jobs are intentionally disabled in `.github/workflows/ci.yml`. Re-enable by reverting the commit that removed them.

## Commands

All commands live in `make`. Run `make help` for the canonical list.

### Development

```bash
make setup              # uv sync, .env, alembic upgrade, create_first_superuser, install pre-commit
make run-backend        # uvicorn app.main:app --reload (localhost:8000)
make run-frontend       # vite (localhost:5173)
make worker             # arq app.core.worker.WorkerSettings
make docker-local       # docker compose -f docker-compose.local.yml up -d (PG + Redis + API + worker + frontend)
make docker-prod        # docker compose -f docker-compose.prod.yml up -d (adds Caddy)
make docker-down        # tear both stacks down
```

### Testing (local only — not in CI)

```bash
make test               # backend pytest
make frontend-test      # Playwright E2E
make test-all           # both
# Single test:
cd backend && uv run pytest tests/path/to/test_file.py::test_function -v
```

### Linting & formatting

```bash
make lint               # ruff check + mypy
make format             # ruff format + ruff check --fix
```

### Database

```bash
make migrate                        # alembic upgrade head
make makemigrations m="description" # alembic revision --autogenerate
```

### Frontend client codegen

```bash
make frontend-gen       # regenerate frontend/src/client/ from backend OpenAPI
```

Run this whenever any backend schema, route, or response model changes. The generated `client/{schemas,sdk,types}.gen.ts` is committed.

## Architecture

### Backend layout (`backend/app/`)

```
api/
  __init__.py           # /api router
  deps.py               # SessionDep, CurrentUser, SuperUserDep, get_optional_user
  routes/               # /api/v1/{health,login,logout,users,items,tasks}
core/
  config.py             # Single flat Settings(BaseSettings). Production-secret guard at import.
  db.py                 # async_engine, local_session, async_get_db
  security.py           # JWT (StrEnum TokenType), bcrypt with configurable rounds, cookie helpers
  setup.py              # lifespan_factory, create_application, NON_BUSINESS_PATHS, _retry_async, _install_metrics
  middleware.py         # RequestLoggingMiddleware (X-Request-ID + structured log line)
  health.py             # check_database_health, check_redis_health
  logger.py             # JsonFormatter → stdout (12-factor)
  exceptions.py         # NotFoundException, ForbiddenException, etc. — use these, not raw HTTPException
  utils/
    queue.py            # ARQ pool reference
    rate_limit.py       # RateLimit dependency, sanitize_path
models/
  base.py               # BaseModel + IDMixin, TimestampMixin, SoftDeleteMixin
  user.py, item.py
schemas/
  users.py              # UserBase, UserRead, UserCreate, UserUpdate (self), UserAdminUpdate, PHONE_PATTERN
  items.py, auth.py, common.py, health.py, base.py, job.py
crud/
  base.py               # BaseCRUD[ModelType]: get/get_multi/exists/count/delete/db_delete + soft-delete auto-filter
  users.py              # CRUDUser: get_by_phone, get_by_username, get_by_login, authenticate
  items.py
tasks/                  # ARQ background tasks; all_tasks list is wired to WorkerSettings.functions
commands/               # CLI entrypoints (e.g. create_first_superuser.py)
migrations/             # Alembic
```

### Key patterns

- **Generic CRUD.** All resources extend `BaseCRUD[ModelType]`. `get_multi` returns a typed `tuple[list[Model], int]` — destructure with `rows, total = await crud.get_multi(...)`. Soft-delete auto-filter is on by default; pass `is_deleted=True` to bypass.
- **Schema-level privilege defence.** `UserUpdate` (self) **does not contain** `is_superuser` / `is_active` / `password`. Pydantic's `extra="ignore"` drops them. `UserAdminUpdate(UserUpdate)` adds them and is only accepted by the superuser-only `PATCH /users/{user_id}` endpoint. Self-updates always go through `PATCH /users/me`.
- **Exception hierarchy.** Use `NotFoundException`, `ForbiddenException`, `DuplicateValueException`, `UnauthorizedException`, `RateLimitException` from `app.core.exceptions`. Don't raise raw `HTTPException` — keep the codebase consistent.
- **Settings.** All tunables in one flat `Settings` class. Magic numbers are not allowed in route or service modules — pull from `settings`.
- **Soft delete.** `BaseModel` includes `is_deleted` + `deleted_at`. CRUD `delete()` is soft; `db_delete()` is hard.

### Frontend layout (`frontend/src/`)

```
client/                 # Auto-generated — DO NOT EDIT (regenerate via make frontend-gen)
routes/                 # TanStack Router file-based
  __root.tsx            # ErrorBoundary + NotFound
  _layout.tsx           # Authenticated shell; readUserMe gate redirects to /login on 401
  login.tsx
  _layout/{index,items,settings,admin}.tsx
components/
  Common/               # ConfirmDialog, DataTable, ErrorComponent, NotFound, AuthLayout, Logo, Footer, Appearance
  Admin/, Items/, UserSettings/, Pending/, Sidebar/
  ui/                   # shadcn-style primitives (Radix wrappers)
hooks/                  # useAuth, useCurrentUser, useCustomToast, useCopyToClipboard, useMobile
lib/
  utils.ts              # cn() helper
  validation.ts         # Shared zod schemas + length/pattern constants — mirrors backend/app/schemas/users.py
queries/                # Centralised TanStack Query options (getItemsQueryOptions, getUsersQueryOptions, getCurrentUserQueryOptions)
main.tsx                # OpenAPI config, axios silent-refresh interceptor, providers
```

### Authentication flow

1. `POST /api/v1/login/access-token` — accepts a username **or** a `+998…` phone in the `username` form field. Returns `{access_token, token_type}` in the body and sets two httpOnly cookies (`access_token`, `refresh_token`) with `samesite="strict"`. `secure=True` in any non-`local` environment.
2. **No JS-accessible token.** The frontend never reads the token; `axios.defaults.withCredentials = true` sends the cookie automatically. `OpenAPI.WITH_CREDENTIALS = true`.
3. On 401, the axios interceptor calls `POST /api/v1/login/refresh` (using the refresh cookie) and retries the original request. Concurrent 401s queue behind one refresh.
4. `/login/refresh` rotates **both** access and refresh tokens to limit the reuse window if a refresh cookie leaks.
5. `POST /api/v1/logout` increments `user.token_version`, which invalidates every outstanding access/refresh token, then clears both cookies.
6. JWT payload: `{sub: <username or +998…>, exp: ..., token_type: "access" | "refresh", token_version: int}`.

### Observability

- Logs are JSON to stdout (`core/logger.py:JsonFormatter`). Promoted extras: `request_id`, `method`, `path`, `status_code`, `duration_ms`.
- Every request gets an `X-Request-ID` (caller-provided or freshly generated). Echoed in the response header.
- Prometheus metrics at `GET /metrics` (`/health`, `/ready`, `/metrics` excluded from the request-count series). **Unauthenticated** — restrict at the proxy in production.
- `/api/v1/health` (liveness) and `/api/v1/ready` (DB + Redis ping) for orchestrators.

### Environment configuration

Copy `.env.example` to `.env`. Defaults are safe for `local`. In `production`, the app refuses to boot if `SECRET_KEY`, `ADMIN_PASSWORD`, `POSTGRES_PASSWORD`, or `ADMIN_PHONE` are still placeholders.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | JWT signing key (`openssl rand -hex 32`) |
| `ENVIRONMENT` | `local`/`staging`/`production` — drives docs gating, cookie `secure`, and prod-secret guard |
| `POSTGRES_*` | Database connection (use `db` host inside Docker) |
| `REDIS_HOST/PORT`, `ENABLE_REDIS_QUEUE`, `ENABLE_REDIS_RATE_LIMIT` | Redis features (toggle independently) |
| `BCRYPT_ROUNDS` | Password hash cost factor (default 12) |
| `LOGIN_RATE_LIMIT_ATTEMPTS`, `LOGIN_RATE_LIMIT_PERIOD` | Brute-force defence on `/login/access-token` |
| `DEFAULT_RATE_LIMIT_LIMIT`, `DEFAULT_RATE_LIMIT_PERIOD` | Default `RateLimit` for state-changing endpoints |
| `DEFAULT_PAGE_SIZE`, `MAX_PAGE_SIZE` | Pagination defaults across all list endpoints |
| `STARTUP_RETRY_MAX_ATTEMPTS`, `STARTUP_RETRY_DELAY_SECONDS` | Lifespan DB/Redis probe retries |
| `THREADPOOL_TOKENS` | AnyIO sync-bridge slots |
| `FORWARDED_ALLOW_IPS` | `ProxyHeadersMiddleware.trusted_hosts`. Default `["*"]` (Caddy in front) |
| `ADMIN_PHONE/USERNAME/PASSWORD` | First superuser created on startup |
| `CORS_ORIGINS`, `CORS_METHODS`, `CORS_HEADERS` | CORS |
| `VITE_API_URL` | Frontend → backend base URL |
| `VITE_API_TIMEOUT_MS` | Axios request timeout (default 30000) |
| `SITE_ADDRESS` | Caddy listener (`:80` plain HTTP, `domain.com` enables auto-HTTPS) |
| `GUNICORN_WORKERS` | Prod uvicorn-worker count |

For Docker dev, set `POSTGRES_SERVER=db` and `REDIS_HOST=redis`.

## Conventions ("don't break these")

- **Email is intentionally removed.** Don't reintroduce an `email` field on the user model or schemas. The boilerplate targets Uzbekistan; phone is universal there. SMS verification can be added on top later — that's a separate feature, not a re-introduction of email.
- **No localStorage tokens.** Auth is cookie-only. Never store the JWT in JS-accessible storage.
- **Refresh rotation stays on.** `_issue_token_pair` runs on every `/refresh`. Don't shortcut this — it's the only thing that limits the reuse window for a leaked refresh cookie.
- **Schema-layer privilege guards.** Don't add `is_superuser`/`is_active` to `UserUpdate`. They live on `UserAdminUpdate` and are only reachable through the superuser-only endpoint.
- **`StrEnum`, not `str + Enum`.** Newer ruff (UP042) flags the latter.
- **Settings only.** Don't hard-code rate limits, page sizes, retry counts, threadpool sizes. Pull from `settings`.
- **Use `CustomException` subclasses.** `from app.core.exceptions import NotFoundException, ForbiddenException, …` — not raw `HTTPException`.
- **Regenerate the client when schemas change.** Stale `frontend/src/client/*.gen.ts` is the most common source of frontend type errors.
- **Tests are local-only in CI.** When you change behaviour, run `make test` / `make frontend-test` locally. Don't quietly disable a test to make a PR pass.

## Pull-request workflow

- Branch off `main`, name with a conventional-commit-style prefix (`fix/…`, `feat/…`, `refactor/…`, `chore/…`).
- One concern per PR. Bundle when there's real cohesion (e.g. "security hardening: rate limit + cookies + proxy headers"); split when there isn't.
- Every PR runs ruff + mypy in CI. Test runs are intentionally local — assume your reviewer expects you to have run them.
- Conventional-commits subject (≤72 chars), body explains the **why**, plus a Test Plan checklist with smoke steps reviewers can mirror.
