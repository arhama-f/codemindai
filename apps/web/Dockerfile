# Build context is the repo root (see docker-compose.yml's `web` service) —
# needed for the root package.json/package-lock.json (npm workspaces) and the
# packages/api-client workspace dependency.
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json
RUN npm ci

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY apps/web apps/web
COPY packages/api-client packages/api-client
# NEXT_PUBLIC_* vars are inlined into the client bundle at build time, not
# read at runtime — must be set here, not just in docker-compose's environment.
ARG NEXT_PUBLIC_API_URL=http://localhost:8010
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build --workspace=apps/web

# `output: "standalone"` (apps/web/next.config.ts) produces a minimal server
# bundle nested under apps/web/ (matching the workspace path) — confirmed by
# actually running the build once, not assumed. Static assets aren't included
# in standalone output and must be copied in separately (no public/ dir
# exists in this app, so nothing to copy there).
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
