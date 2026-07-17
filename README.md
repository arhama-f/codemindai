# CodeMind AI

An AI staff engineer for unfamiliar codebases: connects to a repository, indexes it,
builds a code knowledge graph, answers questions with cited evidence, and (in later
phases) finds bugs, reviews PRs, and proposes fixes.

This repository currently contains the **first vertical slice** only — see
[docs/architecture.md](docs/architecture.md) for what's built and what's
deliberately deferred, and [docs/setup.md](docs/setup.md) for how to run it.

## Quick start

```bash
docker compose up -d
# then follow docs/setup.md from step 2
```

## Repository layout

- `apps/api` — FastAPI backend
- `apps/worker` — arq background worker (repository indexing pipeline)
- `apps/web` — Next.js frontend
- `packages/shared_types` — SQLAlchemy models + cross-service DTOs
- `packages/github_client` — GitHub integration interface + mock implementation
- `packages/code_parser` — tree-sitter based TypeScript/TSX parsing
- `packages/ai_orchestrator` — AI provider interface + mock implementation
- `packages/api-client` — generated TypeScript client for the frontend
- `fixtures/demo-repo` — bundled demo repository used by the mock GitHub client
