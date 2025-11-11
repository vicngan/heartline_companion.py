"""
Notification helpers for push (Expo) + email channels.

Requires environment variables:
- EXPO_ACCESS_TOKEN (optional) for Expo push API.
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD for email channel.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Dict

import requests

EXPO_ENDPOINT = "https://exp.host/--/api/v2/push/send"


class NotificationError(Exception):
    """Raised when a remote notification channel fails."""


def send_expo_notification(token: str, title: str, body: str) -> Dict:
    payload = {"to": token, "sound": "default", "title": title, "body": body}
    headers = {"Content-Type": "application/json"}
    access_token = os.getenv("EXPO_ACCESS_TOKEN")
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    response = requests.post(EXPO_ENDPOINT, json=payload, headers=headers, timeout=10)
    if response.status_code >= 300:
        raise NotificationError(f"Expo push failed: {response.text}")
    data = response.json()
    status = data.get("data", {}).get("status")
    if status == "error":
        message = data.get("data", {}).get("message", "Unknown Expo error")
        raise NotificationError(message)
    return data


def send_email_notification(to_email: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    port = int(os.getenv("SMTP_PORT", "587"))
    if not all([host, user, password]):
        raise NotificationError("Email settings missing. Set SMTP_HOST/SMTP_USER/SMTP_PASSWORD.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
