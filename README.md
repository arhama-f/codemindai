# CodeMind AI

An AI staff engineer for unfamiliar codebases: connects to a repository, indexes it,
builds a code knowledge graph, visualizes architecture, answers questions with cited
evidence (real semantic search), detects bugs/security/performance issues, analyzes
dependency impact, and proposes fixes as draft GitHub pull requests.

This repository currently covers the vertical slice plus three increments (phase 2:
architecture graph, real embeddings, richer explorer; phase 3: bug/security/
performance detection, findings, dependency impact; phase 4: propose-fix generation
via the Claude API and publishing as a draft PR via a GitHub personal access token)
— see [docs/architecture.md](docs/architecture.md) for what's built and what's
deliberately deferred, and [docs/setup.md](docs/setup.md) for how to run it.

## Quick start

```bash
docker compose up -d
# then follow docs/setup.md from step 2
```

## Repository layout

- `apps/api` — FastAPI backend
- `apps/worker` — arq background worker (indexing + analysis pipelines)
- `apps/web` — Next.js frontend
- `packages/shared_types` — SQLAlchemy models + cross-service DTOs
- `packages/github_client` — GitHub read (indexing) + write (publish) interfaces,
  mock implementations, and a real personal-access-token write client
- `packages/code_parser` — tree-sitter based TypeScript/TSX parsing
- `packages/ai_orchestrator` — AI provider interface, a mock implementation, and a
  real Claude API implementation (used for propose-fix only)
- `packages/embedding_provider` — embedding interface + real sentence-transformers implementation
- `packages/analysis_engine` — deterministic bug/security/performance static checks
- `packages/api-client` — generated TypeScript client for the frontend
- `fixtures/demo-repo` — bundled demo repository used by the mock GitHub client
