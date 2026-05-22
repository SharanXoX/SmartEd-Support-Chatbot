"""Escalation: persist ticket + optional webhook."""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import SupportTicket


def create_ticket(
    db: Session,
    *,
    settings: Settings,
    conversation_id: str | None,
    reason: str,
    transcript: list[dict[str, Any]] | None,
    confidence: float | None,
) -> SupportTicket:
    ticket = SupportTicket(
        conversation_id=conversation_id,
        reason=reason,
        transcript_json=transcript,
        confidence_at_escalation=confidence,
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    if settings.escalation_webhook_url:
        try:
            httpx.post(
                settings.escalation_webhook_url,
                json={
                    "ticket_id": ticket.id,
                    "reason": reason,
                    "confidence": confidence,
                    "transcript": transcript,
                },
                timeout=10.0,
            )
        except Exception:
            pass

    return ticket
