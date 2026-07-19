# CodeMind AI — Architecture

This document covers the vertical slice (spec section 27) plus five increments: phase 2
(architecture graph, real embedding-based retrieval, richer source explorer), phase 3
(deterministic bug/security/performance detection, a findings interface, dependency
impact analysis), phase 4 (propose-fix generation and publishing a fix as a draft
GitHub pull request), phase 5 (reviewing an existing GitHub PR's diff: inline
comments + a commit status), and phase 6 (real answer composition for `/ask`, closing
the last mock-templated piece of the ask flow — retrieval had already been real since
phase 2). It intentionally does **not** cover the full 25-section product spec — see
[Deferred](#deferred-to-later-phases) below for what's out of scope and why.

## Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy 2.0 (async, `asyncpg`), Alembic, JWT
  (httponly cookie) + bcrypt auth, arq (Redis-backed async job queue).
- **Worker**: same Python stack, arq worker process running the indexing pipeline.
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind + TanStack Query, calling
  the backend through a generated OpenAPI TypeScript client (`openapi-fetch`).
  `@xyflow/react` for the architecture graph, `prism-react-renderer` for source
  syntax highlighting.
- **Data**: PostgreSQL 16 with `pgvector`, `pgcrypto`, `pg_trgm` extensions; Redis 7.
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim), running
  locally on CPU — free, no API key, and genuinely real semantic search (not a
  template) rather than a paid provider.
- **Local infra**: Docker Compose runs Postgres + Redis only. `apps/api`, `apps/worker`,
  `apps/web` run natively (venv / npm) this round — no Dockerfiles for them yet.

## Monorepo layout

```
codemindai/
├── fixtures/demo-repo/       # bundled demo TS repo served by MockGitHubClient
├── packages/
│   ├── shared_types/         # SQLAlchemy models + cross-service Pydantic DTOs
│   ├── github_client/        # GitHubClient (read) + GitHubWriteClient (write) + Mock/PAT impls
│   ├── code_parser/          # tree-sitter TS/TSX parsing, chunking, import resolution
│   ├── ai_orchestrator/      # AIProvider interface + Mock/Claude impls
│   ├── embedding_provider/   # EmbeddingProvider interface + real sentence-transformers impl
│   ├── analysis_engine/      # tree-sitter based bug/security/performance checks
│   └── api-client/           # generated OpenAPI TS client for the frontend
├── apps/
│   ├── api/                  # FastAPI app (routers, auth, deps)
│   ├── worker/                # arq worker running the indexing pipeline
│   └── web/                  # Next.js frontend
└── infrastructure/docker/    # Postgres init script (extensions + test DB)
```

Domain logic (parsing, GitHub access, AI orchestration) lives in the `packages/`
Python packages, pip-installed editable by both `apps/api` and `apps/worker` — not
inline in route handlers, per the spec's separation-of-concerns rule.

## Database

19 tables across six migrations: the initial schema (`users`, `organizations`,
`organization_members`, `github_installations`, `repositories`, `branches`,
`commits`, `repository_indexes`, `files`, `symbols`, `symbol_relationships`,
`code_chunks`, `embeddings`, `repository_summaries`, `job_runs`); a follow-up
migration (`786118880f25_embeddings_384_dim.py`) that changed `embeddings.vector`
from a placeholder `VECTOR(1536)` (never written to) to `VECTOR(384)` to match the
real embedding model actually chosen; a third migration adding `analysis_runs` and
`findings` (findings' `evidence` is a JSONB column, not a `finding_evidence` join
table — every check produces 1-2 fixed evidence locations known at detection time,
so a join table would buy nothing yet); a fourth adding
`symbol_relationships.confidence` (`confirmed_static` | `unknown`, or `NULL` for
external/unresolved imports) for dependency impact analysis; a fifth
(`d5b2e9f1a4c7_proposed_changes.py`) adding `proposed_changes` for phase 4's
propose-fix workflow — it deliberately has no `original_content`/`file_path`
columns, joining through `file_id` → `files` for both instead, since `File.content`/
`File.path` are already immutable once indexed (same "don't duplicate source of
truth" reasoning as `findings.evidence`); and a sixth
(`e6c3a8d2f9b1_pr_reviews.py`) adding `pr_reviews` for phase 5's PR-review
workflow — deliberately with **no `repository_id` FK** (see the PR-review section
below for why). Every table a route queries directly carries
`organization_id` so tenant isolation is a flat `WHERE organization_id = :org_id`
rather than a multi-hop join. `status`/`kind`/`relationship_type` columns are
`VARCHAR` + `CHECK` (not native `ENUM`) so later phases can add new values without an
`ALTER TYPE` migration. No ANN index (`ivfflat`/`hnsw`) on `embeddings.vector` —
exact brute-force `cosine_distance` search is correct and instant at demo-corpus row
counts; an approximate index would be actively harmful (degenerate recall) this
small and is flagged for when real repo scale exists.

## Core interfaces

**`GitHubClient`** (`packages/github_client`) — `list_installations`,
`list_repositories`, `get_repository_snapshot`. `MockGitHubClient` serves one
hardcoded installation/repo, reading the bundled fixture repo from disk with a fixed
synthetic commit SHA/timestamp (deterministic for tests).

**`AIProvider`** (`packages/ai_orchestrator`) — `summarize_file`,
`summarize_directory`, `identify_subsystems`, `answer_repository_question`,
`propose_fix`, `summarize_pr_review`. `MockAIProvider` is fully
deterministic/template-based (counts and names only, never timestamps or
randomness) so tests assert exact strings. `identify_subsystems` is wired into
the architecture graph endpoint and stays on `MockAIProvider` always — it's
indexing-time summarization, not user-facing generation. `ClaudeAIProvider`
implements three methods for real: `propose_fix` and `summarize_pr_review` write
AI-generated text to a real GitHub PR (phases 4-5); `answer_repository_question`
(phase 6) composes a real answer for `/ask` over already-real (embedding-based)
retrieval from phase 2 — retrieval and composition became real in two separate
rounds, not together, which was an explicit scope boundary at the time, not an
oversight. Its other three methods raise `NotImplementedError` rather than fake a
model call, and indexing-time summarization always stays on `MockAIProvider` (see
the propose-fix, PR-review, and `/ask` sections below). All three real methods are
reached through one provider getter, `get_real_ai_provider()`
(`apps/api/src/codemind_api/providers.py`) — named generically because it now
serves three different call sites, not "for fix" as an earlier, narrower version
of this function was once named.

**`GitHubWriteClient`** (`packages/github_client`) — a separate interface from the
read-only `GitHubClient` above, since indexing (read) and propose-fix/publish/
PR-review (write) are independently swappable and the read path shouldn't need
write credentials. Propose-fix/publish: `get_file`, `create_branch`, `update_file`
(sha-based optimistic concurrency; `sha=None` creates a new file, matching GitHub's
real contents API), `create_pull_request`. PR-review (phase 5): `get_pull_request`,
`get_pull_request_files`, `create_review`, `create_commit_status`.
`MockGitHubWriteClient` is an in-memory store keyed by `(owner, repo, path)`
(files) or `(owner, repo, pr_number)` (PRs), used by all automated tests;
`PATGitHubWriteClient` makes real REST calls against `api.github.com` using a
personal access token, and is never exercised by the automated suite (see the
propose-fix and PR-review sections below).

**`EmbeddingProvider`** (`packages/embedding_provider`) — sibling to `AIProvider`,
not a method on it: embedding and text-generation are independently swappable
choices, and `AIProvider`'s other implementations shouldn't be forced to carry a
torch dependency. `embed(texts: list[str]) -> list[list[float]]`.
`SentenceTransformerEmbeddingProvider` wraps a real, local `all-MiniLM-L6-v2` model
(no API key, ~90MB, downloaded from Hugging Face on first use and cached
thereafter), loaded once and reused via a process-wide `get_default_provider()`
(`@lru_cache` singleton) so the model-load cost is paid once per process, not once
per request or test.

All interfaces are swappable via `apps/api/src/codemind_api/providers.py` — replace
the `Mock*`/`SentenceTransformer*`/`Claude*`/`PAT*` implementation there (and a
config flag) to point at a real GitHub App or a different LLM/embedding provider
later without touching route code. `get_ai_provider_for_fix()` and
`get_github_write_client()` (phase 4) follow the same pattern as the existing
`get_ai_provider()`/`get_embedding_provider()`: both default to their Mock
implementation and only switch to the real one when `ANTHROPIC_API_KEY` /
`GITHUB_PAT` are configured (see `docs/setup.md`).

## Indexing pipeline (`apps/worker/src/codemind_worker/tasks/index_repository.py`)

`index_repository(ctx, *, repository_id, job_run_id)` — same function whether called
directly (as in tests) or via the real arq worker, since all its dependencies
(DB session factory, GitHubClient, AIProvider) come from `ctx`:

1. Fetch repository snapshot from `GitHubClient`.
2. Upsert branch/commit, create a `repository_indexes` row.
3. `code_parser.parse_file()` each `.ts`/`.tsx` file (tree-sitter) → symbols + imports.
4. Insert `files`, `symbols` rows.
5. Resolve import specifiers to known file paths (`resolve_import_path`) → insert
   `symbol_relationships` (`imports` only this round; unresolved/external specifiers
   keep `raw_specifier` with no `to_file_id`).
6. `code_parser.chunk_file()` each file (one chunk per top-level symbol span, plus
   header/trailing chunks, sliding-window fallback for symbol-less files) → insert
   `code_chunks`, then flush to populate their IDs.
7. One batched `EmbeddingProvider.embed()` call over every chunk's content → insert
   `embeddings` rows (`model_name` + 384-dim `vector`).
8. `AIProvider.summarize_file()` per file, rolled up via `summarize_directory()` into
   one `repository_summaries` row per directory plus one repository-root row.
9. Mark the index and job run `completed` with stats (including `embedding_count`);
   any exception marks both `failed` with the error message and re-raises.

Progress percentages are written to `job_runs` at each step so the SSE endpoint has
something to report.

## `/ask` retrieval and answer composition (`apps/api/src/codemind_api/routers/ask.py`)

Real embedding-based semantic search as the top-priority retrieval tier, with the
original lexical approach preserved beneath it as a fallback:

1. Resolve the latest `completed` index for the repo (409 if none).
2. Embed the question (`EmbeddingProvider.embed`) and run a pgvector
   `cosine_distance` query against `embeddings.vector`, ordered ascending, capped at
   3 results, filtered to `distance <= 0.6`. A real embedding model never returns
   "no match" — every chunk has *some* similarity — so this cutoff is what preserves
   "no confident match → empty citations" rather than always returning the 3
   least-dissimilar chunks. 0.6 was measured empirically against the demo repo:
   genuinely relevant matches (including questions with **zero literal keyword
   overlap** with the target code) score ~0.45–0.53; nonsense queries score
   ~0.92–0.98. See `apps/api/tests/test_ask_embeddings.py`.
3. If the embedding tier finds nothing (below the cutoff for all chunks), fall back
   to the original lexical approach: tokenize the question, drop stopwords (fall back
   to raw tokens if that empties the set), SQL `ILIKE` prefilter on
   `code_chunks.content` (`pg_trgm`-indexed, capped at 200 rows), then Python-side
   keyword-count scoring with a +5 bonus if a keyword exactly matches a `symbols.name`
   whose line range falls inside that chunk. Top 3 with score > 0.
4. If that also finds nothing, fall back further to a direct symbol-name `ILIKE`
   match mapped to its enclosing chunk.
5. Build citations (`file_path`, `start_line`, `end_line`, `snippet`) and pass them to
   `AIProvider.answer_repository_question()`, via `get_real_ai_provider()` — Mock's
   deterministic template by default, or a real `claude-opus-4-8` call (plain text,
   no structured output needed for a prose answer) when `ANTHROPIC_API_KEY` is
   configured. The prompt explicitly instructs the model not to reference code
   beyond what's in `citations` and to give an honest "no relevant code was found"
   response when citations is empty, rather than let the model guess from its own
   training data about a repository it can't see.

Always returns 200 with a graceful "couldn't find relevant code" answer and empty
citations when nothing matches at any tier — never a 500 for "no match." Retrieval
became real in phase 2 and answer composition became real later (phase 6) — two
separate rounds, not one; automated tests always exercise the mock (see the
propose-fix section above for why: `get_real_ai_provider()` is overridden to
`MockAIProvider` in every test fixture regardless of `.env` contents).

## Architecture graph (`apps/api/src/codemind_api/routers/architecture.py`)

`GET /api/organizations/{org_id}/repositories/{repo_id}/architecture` returns
file-level nodes (one per `File` row in the latest completed index, annotated with
`identify_subsystems`'s grouping for color-coding), edges from `symbol_relationships`
where `relationship_type == "imports"` (`kind="resolved"` when `to_file_id` is
known, `kind="external"` pointing at one shared synthetic `"external"` node when
it's an unresolved/external specifier — this is what distinguishes observed from
inferred relationships), and `subsystems` metadata separately (used only for
client-side color-coding/legend, not for graph structure — forward-compatible with
a future "collapse to subsystem" UI without an API change). The frontend
(`apps/web/components/ArchitectureGraph.tsx`, `@xyflow/react`) uses a simple
deterministic grid layout keyed by subsystem — no `dagre`/`elkjs` — since a 6-file
demo corpus doesn't need real graph layout; that's flagged as a real-scale TODO in
code.

## Bug/security/performance detection (`packages/analysis_engine`)

Nine deterministic, tree-sitter based static checks — no AI/LLM call involved in
detection itself (matching "AI should enrich deterministic findings, not replace
reliable scanners"). Each check is a plain function `check(path, source, root_node,
symbols) -> list[FindingDraftDTO]`; `codemind_analysis_engine.analyze_file()` parses
once (`code_parser.parse_tree()`) and runs every check against the same tree.
`packages/analysis_engine/src/codemind_analysis_engine/traversal.py` provides the
shared primitives (`find_all`, `enclosing_function`, `node_text`, `line_range`) that
didn't exist before this round — `code_parser` previously only walked top-level
declarations, never into function bodies/expressions.

- **Bugs**: `unsafe-division` (binary `/`/`%` by an identifier with no visible
  zero-guard in the enclosing function — fires on the repo's original planted
  `divide()` bug), `empty-catch-block` (empty `catch` body),
  `unreachable-code-after-return` (statements following a `return`/`throw` in the
  same block).
- **Security**: `hardcoded-secret` (a `const`/`let` whose name matches
  `api[_-]?key|secret|token|password|access[_-]?key` assigned a string literal, not
  `process.env.X`), `unsafe-dangerously-set-inner-html` (JSX `dangerouslySetInnerHTML`
  usage), `sensitive-data-logging` (`console.*()` call with a secret-sounding
  argument name).
- **Performance**: `nested-loop-quadratic` (a loop nested inside another loop),
  `array-scan-in-loop` (`.includes()`/`.indexOf()`/`.find()`/`.findIndex()` called
  inside a loop body), `array-rebuild-in-loop` (`x = [...x, ...y]` inside a loop
  instead of pushing in place).

Every check has a real, intentionally-planted trigger in `fixtures/demo-repo`
(`config.ts`, `utils/collections.ts`, and small additions to `math.ts`,
`userService.ts`, `utils/string.ts`, `UserCard.tsx`) — see
`packages/analysis_engine/tests/` for exact-line-number assertions per check, and
`apps/worker/tests/test_analyze_repository.py` for the full pipeline asserting all 9
fire on the real fixture repo with zero false positives (e.g. a companion
`percentageOf()` with a proper zero-guard next to `divide()` proves the division
check doesn't just fire on every division).

Analysis is a **separate, user-triggered job** (`POST .../analyses` → arq
`analyze_repository` task), not an automatic step of indexing — it reuses the
existing job-type-agnostic `GET /jobs/{id}` + SSE infrastructure via `JobRun.job_type`,
and only needs a DB session (no GitHub/AI/embedding provider), reading already-persisted
`files`/`symbols` from the latest completed index. Findings are grouped under an
`AnalysisRun`; the findings list/detail/dismiss endpoints
(`apps/api/src/codemind_api/routers/findings.py`) always read the latest *completed*
run. Explanation/fix/test text are plain f-string templates built from each check's
own evidence — no `AIProvider` call in this round (see Deferred).

## Dependency impact analysis (`apps/api/src/codemind_api/routers/impact.py`)

`GET .../symbols/{symbol_id}/impact` answers "what breaks if I change this?" —
honestly scoped to **file-level blast radius**, not a true call graph. The indexing
pipeline now resolves `symbol_relationships.to_symbol_id` (previously always `NULL`):
for each imported name, it looks up a same-named exported top-level symbol in the
resolved target file, tagging the relationship `confirmed_static` if found, `unknown`
if the file resolved but no matching export was found (e.g. default export/aliasing),
or leaving `confidence` `NULL` if the import target is external/unresolved. Because a
single import statement can name multiple symbols, one relationship row is now
created per imported name (previously one per import statement) — the architecture
graph endpoint dedupes these back down to one edge per (source, target) file pair so
it isn't affected. The impact endpoint returns direct dependents (files whose
`to_symbol_id` matches) and transitive dependents (files that import *those* files,
one hop further); `from_symbol_id` is deliberately left unpopulated (would need
in-body reference/usage resolution, a materially larger feature), so results are
named `direct_dependent_files`/`transitive_dependent_files`, not `..._symbols`.

## Propose fix / publish workflow (`apps/api/src/codemind_api/routers/proposed_changes.py`)

Phase 4's manually-triggered "propose a fix, then publish it as a draft PR" flow.
Two decisions were locked in explicitly for this round: **no GitHub App/webhooks** —
this environment has no public URL to receive webhooks, so publishing is a personal
access token (PAT) against a real target repo the user configures, triggered by a
button click rather than an automatic PR review; and **real patch generation
requires a real LLM** — a deterministic template can't write plausible code, unlike
the phase 3 findings, so `propose_fix` is the one place this round where an actual
Claude API call happens.

**Scope split** — findings continue to come entirely from the mock-indexed demo
repo; only the *publish* step touches a real external repo, and only when
`GITHUB_TARGET_OWNER`/`GITHUB_TARGET_REPO` are configured. Automated tests never
call the real GitHub or Claude APIs — they exercise `MockGitHubWriteClient`, and
`ClaudeAIProvider` is covered only by construction/shape tests (verifying the exact
`output_config: {"format": {"type": "json_schema", "schema": ...}}` call shape
against the installed `anthropic` SDK, not an actual network call).

1. `POST .../findings/{finding_id}/propose-fix` — loads the finding + its source
   `File`, calls `AIProvider.propose_fix()` (Mock or Claude, via
   `get_ai_provider_for_fix()`), persists the result as a `proposed_changes` row
   with `status="draft"`. `generated_by` records which provider actually ran
   (`isinstance(ai_provider, ClaudeAIProvider)`), not a config flag, so it can't
   drift from reality.
2. `GET .../proposed-changes/{id}` — fetch a proposed change by id.
3. `POST .../proposed-changes/{id}/publish` — 400 if no publish target is
   configured; 409 if already published. Otherwise:
   - **Staleness check**: fetches the target file's *current* remote content via
     `GitHubWriteClient.get_file()` and compares it against the `File.content`
     snapshot the fix was generated from (joined through `proposed_changes.file_id`).
     A mismatch returns 409 rather than silently overwriting a file that changed
     upstream since the fix was proposed — no branch or PR is created in that case.
   - On match: creates a branch (`codemind/fix-{proposed_change_id}`), updates the
     file (using the fetched `sha`), optionally creates a proposed test file
     (`sha=None`, since it's new), and opens a **draft** pull request. Persists
     `status="published"`, `pr_url`, `pr_number`, `published_at`, `published_by`.

The frontend (`ProposedFixPanel.tsx`, on the finding detail page) reuses
`SourceViewer` for a side-by-side original/proposed diff — no new diff library —
and gates publish behind an inline two-step confirmation (not a `window.confirm`,
to match the rest of the app's styling) since it's a hard-to-reverse action against
a real external repo.

## Full PR review (`apps/api/src/codemind_api/routers/pr_review.py`)

Phase 5: reviewing an *existing* GitHub PR's diff — posting inline review comments
and setting a pass/fail commit status, both real GitHub writes, manually triggered
(same "no GitHub App/webhooks" boundary phase 4 locked in — this environment has no
public URL to receive webhooks).

**Checks API vs. Commit Status API — a deliberate substitution, not a partial
implementation.** GitHub's Checks API (rich check-runs with inline annotations) is
GitHub-App-only — it rejects personal access tokens and OAuth tokens outright, and
always has (this is not a recent restriction). Since phase 4 already locked in
PAT-only, this round uses the **Commit Status API**
(`POST /repos/{owner}/{repo}/statuses/{sha}`) instead: a simple pass/fail signal
shown on the PR, without rich inline annotations. Line-level annotations still
happen — just via the (PAT-compatible) Pull Request Reviews API's line comments,
not Checks.

**PR review is org-scoped, not repository-scoped** (`POST
/api/organizations/{org_id}/pr-reviews`, not nested under
`/repositories/{repo_id}/`). The publish target (`GITHUB_TARGET_OWNER/REPO`) is
already a global org-level setting from phase 4, and reviewing PR #N on that real
repo has no meaningful relationship to any CodeMind-tracked (mock-indexed)
`Repository` row — nesting it under one would be misleading. This is also why
`pr_reviews` has no `repository_id` FK.

**Findings are computed fresh, live, from the PR's actual diff** — not from the
mock-indexed demo repo. For each `.ts`/`.tsx` changed file (skipping removed files
and anything without a `patch`): `github_client.diff_utils.parse_patch_added_lines()`
parses the unified-diff hunk headers to find which new-file line numbers are
additions (`+`) — the *only* lines GitHub's Reviews API accepts a line comment on.
The file's real content is fetched at the PR's head ref, run through
`code_parser.parse_file()` + `analysis_engine.analyze_file()` (the same phase 3
checks, called directly and synchronously — no DB, no mock repo involved), and
`analysis_engine.diff_filter.filter_findings_to_added_lines()` keeps only findings
whose `start_line` is an added line — issues actually introduced by this diff, not
pre-existing ones outside it (also a hard API requirement, not just good practice).

Comment bodies reuse existing deterministic finding text (title/severity/
explanation/recommended_fix). One review is posted per PR (not one comment
individually) via `create_review()`, skipped entirely if zero relevant findings
were found (no empty-review spam) — but `create_commit_status()` is always called,
`"failure"` if any relevant finding is `critical`/`high`, else `"success"`. The
review's overall summary paragraph is the one new AI-generated piece this round:
`AIProvider.summarize_pr_review()`, real on `ClaudeAIProvider` (plain-text
`messages.create()` call, no `output_config.format` needed for a prose paragraph)
and deterministic-template on `MockAIProvider`, using the same
`get_ai_provider_for_fix()` toggle phase 4 established (kept as-is despite the
name — it's "the AI provider used for real GitHub-facing generation," now serving
two methods).

No history/list UI this round — `GET /pr-reviews/{id}` exists for future linking,
but there's no list endpoint or page (see Deferred).

## Live job progress

`GET /api/organizations/{org_id}/jobs/{job_id}/events` is a Server-Sent Events stream
(not polling), per the spec's own preference. It polls the DB via short-lived sessions
independent of any single request's session — this matters for tests too: writes made
through a rollback-wrapped test session are invisible to the SSE endpoint's own
connections, so SSE tests use a real (non-rollback) session end-to-end.

## Deferred to later phases

Documented explicitly so it's clear this is scope, not an oversight:

- Real GitHub OAuth/App install flow — needs real GitHub App credentials; phases
  4-5 use a personal access token against a manually-configured target repo instead.
- Webhook-triggered auto-review — this environment has no public URL to receive
  GitHub webhooks; publishing and PR review are both manually triggered instead.
- Rich check-runs via the Checks API — GitHub-App-only, incompatible with the
  PAT-only decision; the Commit Status API is the documented substitute (see the
  Full PR review section above).
- Syncing an updated fix back to an already-published PR (re-publish/amend flow) —
  phase 4 is first-publish-only; amending is a distinct feature.
- PR review history/list UI — schema supports it (`GET /pr-reviews/{id}` +
  `organization_id` scoping), but no list endpoint/page this round.
- Approve/request-changes PR review events — reviews are always posted as
  `COMMENT`; gating merges is the commit status's job, not the review state's.
- Multi-page PR file fetching — `get_pull_request_files` uses the API's default
  page size; a PR with more files than that isn't handled specially yet.
- Making indexing-time summarization real (`summarize_file`, `summarize_directory`,
  `identify_subsystems`) — `ClaudeAIProvider` deliberately doesn't implement these;
  a real call per file/directory during indexing is a different cost/latency
  tradeoff than the three on-demand, user-facing calls that are real (propose-fix,
  PR-review summary, `/ask` answers), and wasn't asked for.
- Automated test coverage of `ClaudeAIProvider`/`PATGitHubWriteClient` against the
  real Claude/GitHub APIs — deliberately excluded from CI (no network calls in
  tests); covered only by manual verification steps with real credentials,
  consistent with the rule against fabricating results.
- Relationship types beyond raw `imports` (`calls`, `extends`, `implements`) in the
  architecture graph — phase 3.
- Multi-level graph clustering / compound-node collapse-expand (repo/module/file
  zoom tiers) — a 6-file demo corpus can't exercise real collapse/expand; the API's
  `subsystems` metadata is forward-compatible with adding this later.
- One node per external package instead of one shared `"external"` node — revisit
  once a real multi-hundred-file repo makes node-count an actual problem.
- Symbol-granularity (`from_symbol_id`) call-graph dependency impact — needs in-body
  reference/usage resolution, a materially larger parser feature; the impact endpoint
  is honestly scoped to file-level blast radius rooted at one exported symbol.
- `probable_dynamic` relationship classification — the parser doesn't see dynamic
  `require()`/computed `import()` at all, so a bucket that could never fire would be
  fabricated, not real.
- DB/network-layer checks (N+1 queries, missing caching, SSRF, path traversal, SQL
  injection) — the TS demo fixture has no DB/HTTP/filesystem-access code to genuinely
  trigger these; faking them would mean synthetic code paths that never exist in the
  actual served repo.
- `AIProvider`-based finding enrichment (e.g. an `explain_finding()` method) — the 9
  checks' explanation/fix/test text are plain templates built from evidence; wiring in
  real LLM enrichment is a clean future addition, not built this round.
- Multi-run findings history UI — the schema supports it (`analysis_run_id` FK on
  `findings`), but the findings list defaults to the latest run only.
- ANN vector index (`ivfflat`/`hnsw`) — harmful/meaningless at demo-corpus row
  counts; flagged for when real repo scale exists.
- Monaco editor — `prism-react-renderer` syntax highlighting plus a symbol outline
  covers this round's "richer source explorer" ask without the complexity of a full
  editor.
- Multi-branch/commit history, PR diffing — single synthetic branch+commit per demo
  repo.
- Playwright as a committed, CI-running E2E suite — every flow (including phase 2's
  architecture graph and semantic `/ask`) was verified manually with one-off
  Playwright scripts during development (see `docs/setup.md`), but no browser E2E
  test is committed to the repo yet.
- Rate limiting, billing/usage, audit logging, notifications, granular RBAC.

## Known local-port remaps

This dev machine already runs other projects' Postgres, Redis, and a service on port
8000. To avoid ambiguity, this project's Docker Compose maps Postgres to host port
**5433** (container 5432) and Redis to host port **6380** (container 6379); the API
runs on **8010** in local dev instead of 8000. See `docker-compose.yml` and
`.env.example`.
