from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from codemind_api.config import settings
from codemind_api.providers import get_embedding_provider
from codemind_api.routers import (
    architecture,
    ask,
    auth,
    files,
    findings,
    github,
    impact,
    indexing,
    organizations,
    repositories,
    summary,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    get_embedding_provider()  # warm the embedding model once at startup, not on first request
    yield
    await app.state.redis_pool.close()


def create_app() -> FastAPI:
    app = FastAPI(title="CodeMind AI API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(organizations.router)
    app.include_router(github.router)
    app.include_router(repositories.router)
    app.include_router(indexing.router)
    app.include_router(files.router)
    app.include_router(summary.router)
    app.include_router(ask.router)
    app.include_router(architecture.router)
    app.include_router(findings.router)
    app.include_router(impact.router)

    return app


app = create_app()
