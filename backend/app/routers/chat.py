"""REST chat endpoints."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Conversation
from app.rate_limit import limiter
from app.schemas import ChatTurnRequest, ChatTurnResponse
from app.services.asset_urls import get_public_base_url
from app.services.chat_service import generate_turn

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("smarted.chat")


def _get_or_create_conversation(db: Session, session_key: str) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.session_key == session_key).first()
    if conv:
        return conv
    conv = Conversation(session_key=session_key, title=None)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.post("/turn", response_model=ChatTurnResponse)
@limiter.limit("45/minute")
def chat_turn(
    request: Request,
    body: ChatTurnRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ChatTurnResponse:
    conv = _get_or_create_conversation(db, body.session_key)
    headers = {k.lower(): v for k, v in request.headers.items()}
    base_url = get_public_base_url(settings, headers)
    lms_ctx: dict | None = None
    if body.lms_context is not None:
        lms_ctx = (
            body.lms_context.model_dump()
            if hasattr(body.lms_context, "model_dump")
            else dict(body.lms_context)
        )
    started = time.perf_counter()
    reply = generate_turn(
        db,
        settings=settings,
        conversation=conv,
        user_message=body.message,
        base_url=base_url,
        current_route=body.current_route,
        lms_context=lms_ctx,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "[CHAT] turn session=%s route=%s mode=%s source=%s %.0fms",
        body.session_key[:12],
        body.current_route or "/",
        reply.response_mode or "unknown",
        reply.response_source or reply.response_type or "unknown",
        elapsed_ms,
    )
    return reply
