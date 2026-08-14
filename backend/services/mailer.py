"""
SMTP email delivery service for contact form inquiries.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Dict, Any

from core.config import settings


class MailService:
    """Dispatches contact submissions via SMTP."""

    @staticmethod
    def send_contact_email(entry: Dict[str, Any]) -> bool:
        host = settings.smtp_host.strip()
        if not host:
            return False

        port = settings.smtp_port
        user = settings.smtp_user.strip()
        password = settings.smtp_password
        to_addr = settings.contact_to_email.strip() or "info@wisef.am"
        from_addr = settings.smtp_from.strip() or (user or "info@wisef.am")
        use_tls = settings.smtp_use_tls

        subject = entry.get("subject") or "Website contact"
        if not subject.lower().startswith("contact"):
            subject = f"Website contact: {subject}"

        body = (
            f"Name: {entry.get('name')}\n"
            f"Email: {entry.get('email')}\n"
            f"Sent: {entry.get('ts')}\n"
            f"IP: {entry.get('ip')}\n\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{entry.get('message')}\n"
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Reply-To"] = entry.get("email") or from_addr
        msg.set_content(body)

        try:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                if use_tls:
                    smtp.starttls()
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
            return True
        except Exception as e:
            print(f"SMTP dispatch error: {e}")
            return False


mail_service = MailService()
