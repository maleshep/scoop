"""Notifications. Email is stubbed until SMTP is configured in .env.

For the PoC, 'notify' just means: the report file is on disk (report.save
already did that). Email fires only when config.email_enabled() is True.
"""
import smtplib
from email.message import EmailMessage

import config


def send_email(subject: str, body_markdown: str) -> None:
    if not config.email_enabled():
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.SMTP["user"]
    msg["To"] = config.SMTP["to"]
    msg.set_content(body_markdown)
    with smtplib.SMTP(config.SMTP["host"], config.SMTP["port"], timeout=20) as s:
        s.starttls()
        s.login(config.SMTP["user"], config.SMTP["pass"])
        s.send_message(msg)


def notify(subject: str, body_markdown: str) -> None:
    send_email(subject, body_markdown)


if __name__ == "__main__":
    print("email_enabled:", config.email_enabled())
