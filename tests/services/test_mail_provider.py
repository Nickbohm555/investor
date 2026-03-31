from app.config import Settings
from app.services.mail_provider import SmtpMailProvider


class FakeSMTP:
    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_calls = []
        self.login_calls = []
        self.messages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self, context=None) -> None:
        self.starttls_calls.append(context)

    def login(self, username: str, password: str) -> None:
        self.login_calls.append((username, password))

    def send_message(self, message) -> None:
        self.messages.append(message)


def test_smtp_mail_provider_sends_email_with_tls_and_login(monkeypatch):
    client = FakeSMTP("smtp.example.com", 587, 30)

    monkeypatch.setattr(
        "app.services.mail_provider.smtplib.SMTP",
        lambda host, port, timeout=30: client,
    )

    provider = SmtpMailProvider(
        Settings(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="investor-user",
            smtp_password="change-me",
            smtp_from_email="investor@example.com",
            daily_memo_to_email="operator@example.com",
        )
    )

    provider.send(
        subject="Investor review for run-123",
        text_body="plain body",
        html_body="<p>html body</p>",
        recipient="operator@example.com",
    )

    assert client.starttls_calls
    assert client.login_calls == [("investor-user", "change-me")]
    assert len(client.messages) == 1
    message = client.messages[0]
    assert message["From"] == "investor@example.com"
    assert message["To"] == "operator@example.com"
    assert message["Subject"] == "Investor review for run-123"
    assert message.get_body(preferencelist=("plain",)).get_content().strip() == "plain body"
    assert message.get_body(preferencelist=("html",)).get_content().strip() == "<p>html body</p>"


def test_smtp_mail_provider_uses_configured_sender_and_recipient(monkeypatch):
    client = FakeSMTP("smtp.example.com", 587, 30)

    monkeypatch.setattr(
        "app.services.mail_provider.smtplib.SMTP",
        lambda host, port, timeout=30: client,
    )

    provider = SmtpMailProvider(
        Settings(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="investor-user",
            smtp_password="change-me",
            smtp_from_email="portfolio@example.com",
            daily_memo_to_email="desk@example.com",
        )
    )

    provider.send(
        subject="Daily memo",
        text_body="plain body",
        html_body="<p>html body</p>",
        recipient="desk@example.com",
    )

    message = client.messages[0]
    assert message["From"] == "portfolio@example.com"
    assert message["To"] == "desk@example.com"


def test_smtp_mail_provider_logs_failure(monkeypatch, caplog):
    class FailingSMTP(FakeSMTP):
        def send_message(self, message) -> None:
            raise RuntimeError("smtp send failed")

    client = FailingSMTP("smtp.example.com", 587, 30)
    monkeypatch.setattr(
        "app.services.mail_provider.smtplib.SMTP",
        lambda host, port, timeout=30: client,
    )

    provider = SmtpMailProvider(
        Settings(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="investor-user",
            smtp_password="change-me",
            smtp_from_email="portfolio@example.com",
            daily_memo_to_email="desk@example.com",
        )
    )

    caplog.set_level("INFO")

    try:
        provider.send(
            subject="Daily memo",
            text_body="plain body",
            html_body="<p>html body</p>",
            recipient="desk@example.com",
        )
    except RuntimeError:
        pass

    assert "memo_delivery result=failure provider=smtp recipient=desk@example.com" in caplog.text
