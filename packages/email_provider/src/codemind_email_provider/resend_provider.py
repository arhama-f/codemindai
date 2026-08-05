import resend

from codemind_email_provider.interface import EmailProvider


class ResendEmailProvider(EmailProvider):
    """Real email provider using the Resend API. Never exercised by the
    automated test suite; only used once RESEND_API_KEY is configured."""

    def __init__(self, *, api_key: str, from_email: str) -> None:
        self._api_key = api_key
        self._from_email = from_email

    async def send(self, *, to: str, subject: str, html_body: str) -> None:
        resend.api_key = self._api_key
        resend.Emails.send(
            {
                "from": self._from_email,
                "to": [to],
                "subject": subject,
                "html": html_body,
            }
        )
