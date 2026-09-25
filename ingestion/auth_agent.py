"""Agent / application access authentication."""

from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


def require_agent_access(
    x_agent_key: str | None = Header(default=None, alias="X-Agent-Key"),
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> None:
    """Allow serving calls with ``X-Agent-Key`` or the ingest webhook secret.

    ``AGENT_ACCESS_SECRET`` wins when set; otherwise ``WEBHOOK_SHARED_SECRET``
    is accepted so one local demo secret covers ingest + serve.
    """
    expected = (
        os.environ.get("AGENT_ACCESS_SECRET", "").strip()
        or os.environ.get("WEBHOOK_SHARED_SECRET", "").strip()
    )
    if not expected:
        return
    presented = (x_agent_key or x_webhook_secret or "").strip()
    if not presented or not hmac.compare_digest(presented, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Agent-Key (or X-Webhook-Secret) header",
        )
