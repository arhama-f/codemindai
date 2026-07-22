# Build context is the repo root (see docker-compose.yml's `api` service) —
# needed to preserve the monorepo layout that apps/api/requirements.txt's
# relative `-e ../../packages/...` entries and config.py's
# `REPO_ROOT = Path(__file__).resolve().parents[4]` both depend on.
FROM python:3.13-slim

WORKDIR /app

# packages/code_parser depends on tree-sitter, which has no prebuilt wheel for
# every platform/Python combo and falls back to compiling from source — needs
# a C compiler. GitHub Actions runners have one preinstalled; this slim image
# doesn't, so install it explicitly (confirmed by an actual failed build, not
# assumed).
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY packages/shared_types packages/shared_types
COPY packages/github_client packages/github_client
COPY packages/code_parser packages/code_parser
COPY packages/ai_orchestrator packages/ai_orchestrator
COPY packages/embedding_provider packages/embedding_provider
COPY apps/api apps/api
COPY fixtures fixtures

RUN pip install --no-cache-dir \
    -e packages/shared_types \
    -e packages/github_client \
    -e packages/code_parser \
    -e packages/ai_orchestrator \
    -e packages/embedding_provider
# cd first: pip resolves a requirements file's relative `-e ../../packages/...`
# entries against the working directory, not the file's own location.
RUN cd apps/api && pip install --no-cache-dir -r requirements.txt -e .

WORKDIR /app/apps/api
EXPOSE 8010

CMD ["sh", "-c", "alembic upgrade head && uvicorn codemind_api.main:app --host 0.0.0.0 --port 8010"]
