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
    # This API's own externally-reachable base URL — used to build OAuth
    # redirect_uri values, which must exactly match what's registered with
    # each provider's app console.
    api_origin: str = "http://localhost:8010"
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

    # Round 7 — email verification / password reset / OAuth login. Unset by
    # default: email stays on MockEmailProvider and OAuth returns 501 until
    # real credentials are configured. See docs/architecture.md.
    resend_api_key: str | None = None
    resend_from_email: str = "noreply@codemind.ai"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None

    # Round 8 — Stripe subscription billing. Unset by default: billing
    # checkout/portal endpoints return 501 until configured.
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id_pro: str | None = None
    stripe_price_id_team: str | None = None

    # Mounts /api/testing/* (inspecting MockEmailProvider's sent emails so the
    # Playwright suite can complete the verification/reset flows without a
    # real inbox). False by default — only set true in playwright.config.ts's
    # webServer env, never in production.
    expose_test_endpoints: bool = False

    # Error monitoring. Unset by default: Sentry is never initialized until a
    # real DSN is configured — same "inert unless configured" convention as
    # every other provider above.
    sentry_dsn: str | None = None


settings = Settings()
