from codemind_email_provider.interface import EmailProvider


class MockEmailProvider(EmailProvider):
    """In-memory email provider for local dev/CI — no real send, deterministic
    and inspectable in tests, matching MockAIProvider/MockGitHubClient."""

    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send(self, *, to: str, subject: str, html_body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "html_body": html_body})
        print(f"[MockEmailProvider] to={to} subject={subject!r}")
