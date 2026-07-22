# Build context is the repo root (see docker-compose.yml's `worker` service) —
# same reasoning as apps/api/Dockerfile: preserves the monorepo layout that
# apps/worker/requirements.txt's relative `-e ../../packages/...` entries and
# deps.py's REPO_ROOT-based default depend on.
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
COPY packages/analysis_engine packages/analysis_engine
COPY apps/worker apps/worker
COPY fixtures fixtures

RUN pip install --no-cache-dir \
    -e packages/shared_types \
    -e packages/github_client \
    -e packages/code_parser \
    -e packages/ai_orchestrator \
    -e packages/embedding_provider \
    -e packages/analysis_engine
# cd first: pip resolves a requirements file's relative `-e ../../packages/...`
# entries against the working directory, not the file's own location.
RUN cd apps/worker && pip install --no-cache-dir -r requirements.txt -e .

WORKDIR /app/apps/worker

CMD ["arq", "codemind_worker.settings.WorkerSettings"]
