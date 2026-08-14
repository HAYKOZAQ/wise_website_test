"""
Contact form submission router.
"""

from __future__ import annotations

import json
import time
import os
import requests
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.security import rate_limiter
from services.mailer import mail_service

router = APIRouter(tags=["Contact"])

BACKEND_DIR = Path(__file__).resolve().parents[1]


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=200)
    subject: str = Field(default="", max_length=300)
    message: str = Field(..., min_length=5, max_length=5000)


@router.post("/api/contact")
def contact_endpoint(payload: ContactRequest, req: Request):
    """Store contact form submissions and optionally dispatch via SMTP/webhook."""
    rate_limiter.check(req)

    name = payload.name.strip()
    email = payload.email.strip()
    subject = (payload.subject or "").strip() or "Website contact"
    message = payload.message.strip()

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Invalid email address")

    client_ip = req.client.host if req.client else "unknown"
    forwarded = req.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ip": client_ip,
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
    }

    data_dir = BACKEND_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = data_dir / "contact_messages.jsonl"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Contact log error: {e}")
        raise HTTPException(status_code=500, detail="Could not save contact message")

    # Dispatch via SMTP if configured
    mail_service.send_contact_email(entry)

    # Optional webhook (e.g., Slack / Discord notifications)
    webhook = (os.environ.get("CONTACT_WEBHOOK_URL") or "").strip()
    if webhook:
        try:
            requests.post(webhook, json=entry, timeout=10)
        except Exception as e:
            print(f"Contact webhook error: {e}")

    return {"ok": True, "message": "Message received"}
