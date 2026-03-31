from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib
import ssl
from typing import Protocol

from app.config import Settings

logger = logging.getLogger(__name__)


class MailProvider(Protocol):
    def send(self, subject: str, text_body: str, html_body: str, recipient: str) -> None:
        ...


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
            with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=30) as client:
                if self._settings.smtp_port == 587:
                    client.starttls(context=ssl.create_default_context())
                if self._settings.smtp_username and self._settings.smtp_password:
                    client.login(self._settings.smtp_username, self._settings.smtp_password)
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
