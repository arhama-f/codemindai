-- Runs once on first container startup (docker-entrypoint-initdb.d).
-- POSTGRES_DB=codemind already exists; create a sibling test database
-- and enable required extensions in both.

CREATE DATABASE codemind_test;

\connect codemind
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\connect codemind_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
