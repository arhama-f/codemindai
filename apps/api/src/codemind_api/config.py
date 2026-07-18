from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://codemind:codemind@localhost:5433/codemind"
    redis_url: str = "redis://localhost:6380/0"
    jwt_secret: str = "dev-secret-change-me-in-production-32bytes-min"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    session_cookie_name: str = "codemind_session"
    web_origin: str = "http://localhost:3000"
    demo_repo_root: str = str(REPO_ROOT / "fixtures" / "demo-repo")

    # Round 4 — propose-fix / publish workflow. Unset by default: both stay on
    # their Mock implementations until real credentials are configured. See
    # docs/architecture.md for the mock-indexed/real-publish-target split.
    anthropic_api_key: str | None = None
    github_pat: str | None = None
    github_target_owner: str | None = None
    github_target_repo: str | None = None
    github_target_base_branch: str = "main"
    # Prepended to a File's indexed path (e.g. "src/utils/math.ts") when
    # calling the real GitHub API, for target repos where the indexed source
    # tree lives under a subdirectory rather than at the repo root.
    github_target_path_prefix: str = ""


settings = Settings()
