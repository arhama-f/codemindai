# Setup

## Prerequisites

- Docker Desktop (for Postgres + Redis)
- Python 3.11+ (developed against 3.13)
- Node.js 20+ (developed against 24) and npm

## 1. Start Postgres + Redis

```bash
docker compose up -d
docker compose ps   # both should show "healthy"
```

This maps Postgres to host port **5433** and Redis to host port **6380** (not the
defaults — see [architecture.md](architecture.md#known-local-port-remaps)) and runs
`infrastructure/docker/postgres/init-extensions.sql` once, which creates the
`codemind` and `codemind_test` databases with the `vector`, `pgcrypto`, and `pg_trgm`
extensions enabled in both.

## 2. Backend — API

```bash
python3 -m venv .venv
source .venv/bin/activate

cd apps/api
pip install -e ../../packages/shared_types -e ../../packages/github_client \
            -e ../../packages/code_parser -e ../../packages/ai_orchestrator \
            -e ../../packages/embedding_provider
pip install -r requirements-dev.txt
pip install -e .

alembic upgrade head
ALEMBIC_DATABASE_URL="postgresql+psycopg2://codemind:codemind@localhost:5433/codemind_test" \
  alembic upgrade head   # migrate the test DB too

uvicorn codemind_api.main:app --port 8010
```

`packages/embedding_provider` pulls in `sentence-transformers` (and `torch` — a
large download, several hundred MB). The first time the app starts (or the first
test run that touches embeddings), it also downloads the `all-MiniLM-L6-v2` model
weights (~90MB) from Hugging Face and caches them under `~/.cache/huggingface` —
this needs network access once; subsequent starts/runs are fast (model loads from
the local cache in a couple of seconds).

`GET http://localhost:8010/healthz` should return `{"status": "ok"}`, and
`http://localhost:8010/docs` serves the interactive API docs.

## 3. Backend — Worker

In a second terminal (same venv):

```bash
cd apps/worker
pip install -r requirements-dev.txt -e .
arq codemind_worker.settings.WorkerSettings
```

## 4. Frontend

```bash
cd packages/api-client
npm install
npm run generate   # regenerate the TS client from apps/api's current OpenAPI schema

cd ../../   # repo root
npm install        # installs apps/web + packages/api-client via npm workspaces

cd apps/web
cp .env.example .env.local
npm run dev
```

Visit `http://localhost:3000`.

## 5. Run tests

```bash
# Backend (from the venv, needs Postgres/Redis running)
cd apps/api && python -m pytest tests/ -q
cd apps/worker && python -m pytest tests/ -q
cd packages/analysis_engine && python -m pytest tests/ -q
cd packages/embedding_provider && python -m pytest tests/ -q

# Frontend
cd apps/web && npx vitest run
cd apps/web && npx tsc --noEmit
```

## 6. Try the full flow

1. Register at `/register`, create an organization at `/orgs/new`.
2. On the organization page, click **Connect GitHub (mock)**, then **Add** the
   `codemind-demo/todo-app-ts` demo repository.
3. On the repository page, click **Run indexing** and watch the live progress bar
   (Server-Sent Events) until it shows "Indexed".
4. Click **Architecture** to see the file-level import graph, color-coded by
   subsystem.
5. Click **Explore files** to browse the directory tree; open a file to see
   syntax-highlighted source with a clickable symbol outline.
6. Click **Ask a question** and try something with **no literal keyword overlap**
   with the code, e.g. *"how do I split a number into pieces?"* — it should still
   cite `src/utils/math.ts`'s `divide` function, proving retrieval is genuinely
   semantic (via real embeddings), not just keyword matching.
7. Click **Findings**, then **Run analysis** and watch the progress bar. When it
   completes, 9 real findings should appear (3 bugs, 3 security, 3 performance).
   Open one to see its evidence/explanation/recommended fix, and try dismissing it
   with a reason — it should disappear from the default "open" filter.
8. Back in **Explore files**, open `src/utils/math.ts`, and click **impact** next to
   the `divide` symbol in the outline — it should show `src/index.ts` as a direct,
   `confirmed_static` dependent.

## Regenerating the API client after backend changes

Whenever routes change, re-export the OpenAPI schema and regenerate the TS client:

```bash
cd apps/api && python scripts/export_openapi.py
cd ../../packages/api-client && npm run generate
```

## Known limitations

- No Dockerfiles for `apps/api`/`apps/worker`/`apps/web` yet — they run natively.
- No committed browser E2E test suite — the onboarding→ask flow was verified with a
  one-off local Playwright script during development, not a repo-committed test.
- Mock GitHub/AI providers only — see `docs/architecture.md` for what's deferred and
  why.
