"""Webhook authentication via shared secret header."""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


def require_webhook_secret(
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> None:
    """Reject requests that do not present the configured shared secret.

    In development, if ``WEBHOOK_SHARED_SECRET`` is empty, auth is skipped
    (logged by the caller). Production must set a non-empty secret.
    """
    expected = os.environ.get("WEBHOOK_SHARED_SECRET", "").strip()
    if not expected:
        return
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Webhook-Secret header",
        )
