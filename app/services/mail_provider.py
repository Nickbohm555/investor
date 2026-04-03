from __future__ import annotations

from contextlib import contextmanager
from email.message import EmailMessage
import logging
import smtplib
import ssl
from typing import Iterator, Protocol

from app.config import Settings

logger = logging.getLogger(__name__)


class MailProvider(Protocol):
    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        ...


def _resolve_smtp_transport_mode(settings: Settings) -> str:
    if settings.smtp_security == "starttls":
        if settings.smtp_port != 587:
            raise ValueError("Unsupported SMTP transport mode")
        return "starttls"
    if settings.smtp_security == "ssl":
        if settings.smtp_port != 465:
            raise ValueError("Unsupported SMTP transport mode")
        return "ssl"
    if settings.smtp_security == "auto":
        if settings.smtp_port == 587:
            return "starttls"
        if settings.smtp_port == 465:
            return "ssl"
    raise ValueError("Unsupported SMTP transport mode")


@contextmanager
def smtp_client_session(settings: Settings) -> Iterator[smtplib.SMTP]:
    mode = _resolve_smtp_transport_mode(settings)
    context = ssl.create_default_context()

    if mode == "ssl":
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=30,
            context=context,
        ) as client:
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            yield client
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as client:
        client.starttls(context=context)
        if settings.smtp_username and settings.smtp_password:
            client.login(settings.smtp_username, settings.smtp_password)
        yield client


def inspect_smtp_connection(settings: Settings) -> dict[str, object]:
    mode = _resolve_smtp_transport_mode(settings)
    with smtp_client_session(settings):
        pass
    return {
        "host": settings.smtp_host,
        "port": settings.smtp_port,
        "transport_mode": mode,
        "uses_starttls": mode == "starttls",
    }


class SmtpMailProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._settings.smtp_from_email
        message["To"] = recipient
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")

        try:
            with smtp_client_session(self._settings) as client:
                client.send_message(message)
        except Exception:
            logger.exception(
                "memo_delivery result=failure provider=smtp recipient=%s",
                recipient,
            )
            raise
        logger.info(
            "memo_delivery result=sent provider=smtp recipient=%s",
            recipient,
        )
