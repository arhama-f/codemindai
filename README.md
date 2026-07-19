# CodeMind AI

An AI staff engineer for unfamiliar codebases: connects to a repository, indexes it,
builds a code knowledge graph, visualizes architecture, answers questions with cited
evidence (real semantic search), detects bugs/security/performance issues, analyzes
dependency impact, proposes fixes as draft GitHub pull requests, and reviews existing
PRs with inline comments and a commit status.

This repository currently covers the vertical slice plus four increments (phase 2:
architecture graph, real embeddings, richer explorer; phase 3: bug/security/
performance detection, findings, dependency impact; phase 4: propose-fix generation
via the Claude API and publishing as a draft PR; phase 5: reviewing an existing PR's
diff with inline comments + a commit status — both via a GitHub personal access
token) — see [docs/architecture.md](docs/architecture.md) for what's built and
what's deliberately deferred, and [docs/setup.md](docs/setup.md) for how to run it.

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
- `packages/github_client` — GitHub read (indexing) + write (publish, PR review)
  interfaces, mock implementations, and a real personal-access-token write client
- `packages/code_parser` — tree-sitter based TypeScript/TSX parsing
- `packages/ai_orchestrator` — AI provider interface, a mock implementation, and a
  real Claude API implementation (propose-fix and PR-review summaries)
- `packages/embedding_provider` — embedding interface + real sentence-transformers implementation
- `packages/analysis_engine` — deterministic bug/security/performance static checks,
  used both by the indexing pipeline and live against a PR's diff for PR review
- `packages/api-client` — generated TypeScript client for the frontend
- `fixtures/demo-repo` — bundled demo repository used by the mock GitHub client
