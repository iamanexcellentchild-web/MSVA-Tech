"""
Send Django emails through Brevo's HTTPS API.

Render's free plan blocks outbound SMTP ports (25/465/587), so the usual Gmail
SMTP backend can't connect. Brevo's transactional API works over HTTPS (port 443).
Free plan: 300 emails/day. Set BREVO_API_KEY to switch this backend on.
"""

import logging
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def _contact(address):
    name, email = parseaddr(address)
    return {"email": email, **({"name": name} if name else {})}


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            html = next((body for body, mime in getattr(message, "alternatives", []) if mime == "text/html"), None)
            payload = {
                "sender": _contact(message.from_email or settings.DEFAULT_FROM_EMAIL),
                "to": [_contact(addr) for addr in message.to],
                "subject": message.subject,
                "textContent": message.body,
            }
            if html:
                payload["htmlContent"] = html
            if message.cc:
                payload["cc"] = [_contact(addr) for addr in message.cc]
            if message.bcc:
                payload["bcc"] = [_contact(addr) for addr in message.bcc]
            if message.reply_to:
                payload["replyTo"] = _contact(message.reply_to[0])
            try:
                resp = requests.post(
                    BREVO_URL, json=payload, timeout=15,
                    headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
                )
                resp.raise_for_status()
                sent += 1
            except requests.RequestException as exc:
                detail = getattr(getattr(exc, "response", None), "text", "")[:300]
                logger.error("Brevo send failed: %s %s", exc, detail)
                if not self.fail_silently:
                    raise
        return sent
