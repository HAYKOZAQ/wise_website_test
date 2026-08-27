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

        plain_body = (
            f"New Contact Message from WISE Website\n"
            f"-------------------------------------\n"
            f"Name: {entry.get('name')}\n"
            f"Email: {entry.get('email')}\n"
            f"Date/Time: {entry.get('ts')}\n"
            f"IP Address: {entry.get('ip')}\n\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{entry.get('message')}\n"
        )

        html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
  <h2 style="color: #0f172a; border-bottom: 2px solid #f5ba35; padding-bottom: 8px; margin-top: 0;">Նոր հաղորդագրություն կայքից (WISE)</h2>
  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr><td style="padding: 6px 0; font-weight: bold; width: 120px; color: #64748b;">Ուղարկող:</td><td style="padding: 6px 0;">{entry.get('name')}</td></tr>
    <tr><td style="padding: 6px 0; font-weight: bold; color: #64748b;">Էլ. փոստ:</td><td style="padding: 6px 0;"><a href="mailto:{entry.get('email')}" style="color: #2563eb;">{entry.get('email')}</a></td></tr>
    <tr><td style="padding: 6px 0; font-weight: bold; color: #64748b;">Թեմա:</td><td style="padding: 6px 0;">{subject}</td></tr>
    <tr><td style="padding: 6px 0; font-weight: bold; color: #64748b;">Ամսաթիվ:</td><td style="padding: 6px 0;">{entry.get('ts')}</td></tr>
  </table>
  <div style="background: #f8fafc; border-left: 4px solid #f5ba35; padding: 16px; border-radius: 4px; margin-top: 12px;">
    <h4 style="margin: 0 0 8px 0; color: #334155;">Հաղորդագրություն:</h4>
    <p style="white-space: pre-wrap; margin: 0; color: #0f172a;">{entry.get('message')}</p>
  </div>
  <p style="font-size: 12px; color: #94a3b8; margin-top: 24px; text-align: center;">Այս նամակն ավտոմատ ուղարկվել է wisef.am կայքի կոնտակտային ձևից:</p>
</body>
</html>"""

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Reply-To"] = entry.get("email") or from_addr
        msg.set_content(plain_body)
        msg.add_alternative(html_body, subtype="html")

        try:
            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=15) as smtp:
                    if user:
                        smtp.login(user, password)
                    smtp.send_message(msg)
            else:
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
