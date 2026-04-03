from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import mail_provider


def _build_settings(*, smtp_port: int, smtp_security: str = "auto") -> SimpleNamespace:
    return SimpleNamespace(
        smtp_host="smtp.example.com",
        smtp_port=smtp_port,
        smtp_security=smtp_security,
        smtp_username="smtp-user",
        smtp_password="smtp-pass",
        smtp_from_email="investor@example.com",
    )


def test_smtp_mail_provider_uses_starttls_on_port_587(monkeypatch) -> None:
    events: list[tuple[str, object]] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            events.append(("connect", (host, port, timeout)))

        def __enter__(self) -> FakeSMTP:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def starttls(self, *, context) -> None:
            events.append(("starttls", context))

        def login(self, username: str, password: str) -> None:
            events.append(("login", (username, password)))

        def send_message(self, message) -> None:
            events.append(("send_message", message["To"]))

    def unexpected_smtp_ssl(*args, **kwargs):
        raise AssertionError("SMTP_SSL should not be used on port 587")

    monkeypatch.setattr(mail_provider.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(mail_provider.smtplib, "SMTP_SSL", unexpected_smtp_ssl)

    provider = mail_provider.SmtpMailProvider(_build_settings(smtp_port=587))

    provider.send("Subject", "Plain", "<p>HTML</p>", "operator@example.com")

    assert ("connect", ("smtp.example.com", 587, 30)) in events
    assert any(event[0] == "starttls" for event in events)
    assert ("login", ("smtp-user", "smtp-pass")) in events
    assert ("send_message", "operator@example.com") in events


def test_smtp_mail_provider_uses_smtp_ssl_on_port_465(monkeypatch) -> None:
    events: list[tuple[str, object]] = []

    def unexpected_smtp(*args, **kwargs):
        raise AssertionError("SMTP should not be used on port 465")

    class FakeSMTPSSL:
        def __init__(self, host: str, port: int, timeout: int, context) -> None:
            events.append(("connect_ssl", (host, port, timeout, context)))

        def __enter__(self) -> FakeSMTPSSL:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def login(self, username: str, password: str) -> None:
            events.append(("login", (username, password)))

        def send_message(self, message) -> None:
            events.append(("send_message", message["To"]))

    monkeypatch.setattr(mail_provider.smtplib, "SMTP", unexpected_smtp)
    monkeypatch.setattr(mail_provider.smtplib, "SMTP_SSL", FakeSMTPSSL)

    provider = mail_provider.SmtpMailProvider(_build_settings(smtp_port=465))

    provider.send("Subject", "Plain", "<p>HTML</p>", "operator@example.com")

    assert any(event[0] == "connect_ssl" for event in events)
    assert ("login", ("smtp-user", "smtp-pass")) in events
    assert ("send_message", "operator@example.com") in events


def test_smtp_mail_provider_raises_clear_error_for_unsupported_transport_mode() -> None:
    provider = mail_provider.SmtpMailProvider(_build_settings(smtp_port=2525, smtp_security="ssl"))

    with pytest.raises(ValueError, match="Unsupported SMTP transport mode"):
        provider.send("Subject", "Plain", "<p>HTML</p>", "operator@example.com")
