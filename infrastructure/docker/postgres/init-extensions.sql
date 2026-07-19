-- Runs once on first container startup (docker-entrypoint-initdb.d).
-- POSTGRES_DB=codemind already exists; create sibling databases for the
-- pytest suite (rollback-per-test, never persists) and the Playwright E2E
-- suite (real persisted rows, isolated from the dev DB), and enable required
-- extensions in all three.

CREATE DATABASE codemind_test;
CREATE DATABASE codemind_e2e;

\connect codemind
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\connect codemind_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\connect codemind_e2e
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
