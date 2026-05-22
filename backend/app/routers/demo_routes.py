"""Public demo endpoints: mock student profile and support tickets."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Conversation, Message
from app.rate_limit import limiter
from app.schemas import SupportTicketCreate, SupportTicketOut
from app.services.escalation_service import create_ticket
from app.services.lms_feature_registry import AVAILABLE_LMS_FEATURES, AVAILABLE_LMS_ROUTES
from app.services.mock_data_loader import list_student_profiles, load_student_state, upcoming_exams
from app.services.student_context import get_mock_student

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/students")
def demo_student_list() -> dict[str, Any]:
    return {"students": list_student_profiles()}


@router.get("/student")
def demo_student(
    settings: Annotated[Settings, Depends(get_settings)],
    student_id: str | None = Query(default=None, max_length=64),
) -> dict[str, Any]:
    data = get_mock_student(settings, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Mock student context disabled")
    return data


@router.get("/lms-state")
def demo_lms_state(
    settings: Annotated[Settings, Depends(get_settings)],
    student_id: str | None = Query(default=None, max_length=64),
    current_route: str | None = Query(default=None, max_length=512),
) -> dict[str, Any]:
    data = get_mock_student(settings, student_id)
    if not data:
        raise HTTPException(status_code=404, detail="Mock student context disabled")
    return {
        "student": data,
        "courses": data.get("courses") or [],
        "exams": data.get("exams") or [],
        "upcoming_exams": upcoming_exams(data),
        "purchases": data.get("purchases") or [],
        "certificates": data.get("certificates") or [],
        "announcements": data.get("announcements") or [],
        "recent_activity": data.get("recent_activity") or [],
        "available_features": list(AVAILABLE_LMS_FEATURES),
        "available_routes": dict(AVAILABLE_LMS_ROUTES),
        "current_route": current_route,
    }


@router.post("/support/ticket", response_model=SupportTicketOut)
@limiter.limit("20/minute")
def create_support_ticket(
    request: Request,
    body: SupportTicketCreate,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SupportTicketOut:
    conversation_id: str | None = None
    transcript: list[dict[str, str]] = []
    if body.session_key:
        conv = db.query(Conversation).filter(Conversation.session_key == body.session_key).first()
        if conv:
            conversation_id = conv.id
            msgs = (
                db.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(Message.created_at.asc())
                .limit(40)
                .all()
            )
            transcript = [{"role": m.role, "content": m.content} for m in msgs]

    reason = (
        f"Student support ticket\n"
        f"Name: {body.name}\n"
        f"Email: {body.email}\n\n"
        f"Issue:\n{body.issue}"
    )
    ticket = create_ticket(
        db,
        settings=settings,
        conversation_id=conversation_id,
        reason=reason,
        transcript=transcript or None,
        confidence=None,
    )
    return SupportTicketOut(id=ticket.id, status=ticket.status)
