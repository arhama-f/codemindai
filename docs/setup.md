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
            -e ../../packages/embedding_provider -e ../../packages/analysis_engine
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
   semantic (via real embeddings), not just keyword matching. Without real
   credentials configured (see below), the answer text is a deterministic
   template; with `ANTHROPIC_API_KEY` set, it's a real Claude-composed answer.
7. Click **Findings**, then **Run analysis** and watch the progress bar. When it
   completes, 9 real findings should appear (3 bugs, 3 security, 3 performance).
   Open one to see its evidence/explanation/recommended fix, and try dismissing it
   with a reason — it should disappear from the default "open" filter.
8. Back in **Explore files**, open `src/utils/math.ts`, and click **impact** next to
   the `divide` symbol in the outline — it should show `src/index.ts` as a direct,
   `confirmed_static` dependent.
9. On a finding's detail page, click **Propose fix** — a mock-generated explanation
   and a side-by-side original/proposed diff should appear. Click **Publish as draft
   PR**, then **Confirm publish** — without real credentials configured (see below),
   this correctly shows *"No publish target configured"* rather than silently
   succeeding.
10. Back on the organization page, under **Review a GitHub PR**, enter a PR number
    and click **Review PR**, then **Confirm review** — same as step 9, without real
    credentials this correctly shows *"No target repo configured"*.

## Real credentials for propose-fix / publish / PR review / `/ask` (optional)

By default, propose-fix, PR-review summaries, and `/ask` answers all use
`MockAIProvider`, and publish/PR-review writes use `MockGitHubWriteClient` —
nothing leaves your machine. `ANTHROPIC_API_KEY` alone is enough to make `/ask`
answers real (no GitHub target needed, since `/ask` only reads from the
already-indexed mock repo). To also exercise real GitHub writes (publish,
PR review), set these in `apps/api/.env` (create it if it doesn't exist) and
restart the API server:

```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_PAT=ghp_...                # fine-grained PAT with Contents: Read and write
GITHUB_TARGET_OWNER=your-username
GITHUB_TARGET_REPO=your-test-repo
GITHUB_TARGET_BASE_BRANCH=main    # optional, defaults to "main"
GITHUB_TARGET_PATH_PREFIX=        # optional, prepended to indexed paths (e.g. "docs/" if the
                                   # target repo has the mirrored source under a subdirectory)
```

`GITHUB_TARGET_REPO` must be seeded with content matching `fixtures/demo-repo/src`
(same file paths/content, optionally under `GITHUB_TARGET_PATH_PREFIX`) — the
publish endpoint fetches the file from this real repo and 409s if its content
doesn't match what the fix was generated from. This is never exercised by the
automated test suite; treat it as a manual, one-off check — publishing creates a
real branch and opens a real draft PR. (Verified end-to-end against
`arhama-f/codemindai` itself using `GITHUB_TARGET_PATH_PREFIX=fixtures/demo-repo/`,
since that repo's own fixture directory already mirrors the indexed content.)

`GITHUB_TARGET_PATH_PREFIX` does **not** apply to PR review — reviewing PR #N
fetches that PR's real files directly from GitHub, whose paths are already correct
as returned by the API (no CodeMind-index-relative stripping to undo). Reviewing a
PR also creates real writes (a review comment + a commit status) on that PR — same
one-off, never-automated verification approach as publish.

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
- Mock GitHub/AI providers by default — real `ClaudeAIProvider`/`PATGitHubWriteClient`
  are wired in but only used for `propose_fix`/publish, and only when real
  credentials are configured (see "Real credentials" above). See
  `docs/architecture.md` for what else is deferred and why.
