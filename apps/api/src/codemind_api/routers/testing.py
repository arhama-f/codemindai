from fastapi import APIRouter, Depends, HTTPException, status

from codemind_api.providers import get_email_provider
from codemind_email_provider import EmailProvider, MockEmailProvider

router = APIRouter(prefix="/api/testing", tags=["testing"])


@router.get("/last-email")
async def last_email(to: str, email_provider: EmailProvider = Depends(get_email_provider)) -> dict:
    """Only mounted when settings.expose_test_endpoints is true (Playwright's
    webServer env) — lets E2E tests complete the verification/reset flows by
    reading the token MockEmailProvider would otherwise only log to console."""
    if not isinstance(email_provider, MockEmailProvider):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No mock email provider active")
    matching = [sent for sent in email_provider.sent if sent["to"] == to]
    if not matching:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No email sent to this address")
    return matching[-1]
