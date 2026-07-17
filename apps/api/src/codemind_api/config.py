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


settings = Settings()
