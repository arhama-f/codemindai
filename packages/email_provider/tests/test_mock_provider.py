from codemind_email_provider import MockEmailProvider


async def test_mock_provider_records_sent_emails():
    provider = MockEmailProvider()

    await provider.send(to="user@example.com", subject="Verify your email", html_body="<p>hi</p>")

    assert provider.sent == [
        {
            "to": "user@example.com",
            "subject": "Verify your email",
            "html_body": "<p>hi</p>",
        }
    ]
