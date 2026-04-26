# 🚀 FastAPI Fullstack Boilerplate

A **lean, modern full-stack boilerplate** for building real products fast — without overengineering or heavy infrastructure.

Built for **solo developers, freelancers, and small teams** who want a codebase that is **easy to understand, easy to change, and fast to ship**.

---

## 🎯 What This Is

- ⚡ **Minimal-infra** FastAPI + React, one Caddy proxy in front in prod.
- 📞 **Phone-first auth** — login with username **or** an Uzbekistan E.164 phone (`+998…`). Email is intentionally absent.
- 🔐 **Real auth hardening** — httpOnly cookies (`samesite=strict`), refresh-token rotation, login rate limit, `token_version` revocation, schema-layer privilege guards.
- 📈 **Production observability** — JSON logs to stdout, `X-Request-ID` echoed on every response, Prometheus `/metrics`, `/health` + `/ready` probes.
- 🛠 **Built to be modified, not worshipped.** If you usually delete half of a boilerplate on day one, this starts closer to what you actually need.

---

## 🧩 Core Stack

**Backend** (Python 3.11+)
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async, asyncpg) + Alembic
- PostgreSQL · Redis · ARQ background jobs
- JWT (`pyjwt`) · bcrypt
- gunicorn + uvicorn workers in prod
- `prometheus-fastapi-instrumentator` for `/metrics`
- `uv` for dependency management

**Frontend** (Node 24+)
- React 19 + Vite 7 + SWC
- TanStack Router (file-based, auto code-split) + TanStack Query
- Tailwind v4 + Radix + shadcn-style primitives + `next-themes`
- `react-hook-form` + `zod`
- Auto-generated TypeScript client from the backend OpenAPI spec
- Biome for lint + format

**Infra & tooling**
- Docker Compose: `docker-compose.local.yml` for dev, `docker-compose.prod.yml` for prod (Caddy reverse proxy with `SITE_ADDRESS` env-templated → auto-HTTPS via Let's Encrypt when a domain is set).
- Pre-commit hooks: ruff + mypy + biome.
- Dependabot configured for `uv`, `npm`, `github-actions`, and `docker` (minor/patch grouped, risky majors opt out).
- GitHub Actions CI runs ruff + mypy. Pytest and Playwright suites live in the repo and run locally; the CI jobs are intentionally disabled — re-enable by reverting the commit that removed them.

---

## ⚡ Quick start

```bash
# 1. Clone + setup (copies .env, syncs deps, runs migrations, creates superuser, installs hooks)
git clone https://github.com/apayziev/boilerplate
cd boilerplate
make setup

# 2. Run the stack (PG + Redis + API + worker + frontend)
make docker-local

# 3. Log in to http://localhost:3000
#    Username: admin   (or phone: +998901234567)
#    Password: Change-me   (set in .env via ADMIN_PASSWORD)
```

Or run pieces directly without Docker: `make run-backend`, `make run-frontend`, `make worker`.

The full command list lives in `Makefile` (`make help`).

---

## 🧠 Design Principles

- 🪶 **Low infrastructure cost.** Postgres + Redis + Caddy. No service mesh, no Kafka, no Kubernetes manifests.
- 🧱 **Few moving parts.** One backend, one worker, one frontend. One reverse proxy in prod.
- 📖 **Readable over clever.** Generic CRUD when it earns its keep, inline code when it doesn't.
- 🚫 **No enterprise cosplay.** Settings are flat. Magic numbers live in `.env`. Privilege escalation is impossible at the schema layer, not by careful handler discipline.
- 🌍 **Built around phone numbers, not email.** Defaults match the Uzbek market. SMS verification is an obvious next step but isn't bundled.

---

## 👤 Who This Is For

- 🚀 MVP builders
- 🧑‍💻 Freelancers shipping client projects
- 🧠 Founders validating ideas
- 👥 Small teams that want control

If you need GraphQL, multi-tenancy, OAuth federation, or a microservice mesh out of the box — this isn't that.

---

## 📜 License

MIT — use it, fork it, strip it down, or build on top of it.

---

**In short:** this boilerplate stays small so your product doesn't have to fight it.
