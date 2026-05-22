"""WebSocket streaming chat."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Conversation
from app.services.chat_service import generate_turn, stream_reply_chunks
from app.config import get_settings

router = APIRouter(tags=["websocket"])


def _get_conv(db: Session, session_key: str) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.session_key == session_key).first()
    if conv:
        return conv
    conv = Conversation(session_key=session_key, title=None)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.websocket("/ws/chat/{session_key}")
async def chat_socket(websocket: WebSocket, session_key: str) -> None:
    await websocket.accept()
    settings = get_settings()

    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            message = str(payload.get("message") or "").strip()
            if not message:
                await websocket.send_json({"type": "error", "detail": "empty message"})
                continue

            db = SessionLocal()
            try:
                conv = _get_conv(db, session_key)
                turn = generate_turn(
                    db,
                    settings=settings,
                    conversation=conv,
                    user_message=message,
                    base_url="",
                )
                is_walkthrough = turn.response_source == "support_flow" and len(turn.visual_steps) > 0
                if not is_walkthrough:
                    for chunk in stream_reply_chunks(turn.reply):
                        await websocket.send_json({"type": "token", "content": chunk})
                        await asyncio.sleep(0.012)
                await websocket.send_json(
                    {
                        "type": "done",
                        "payload": {
                            "intent": turn.intent,
                            "confidence": turn.confidence,
                            "visual_steps": [vs.model_dump() for vs in turn.visual_steps],
                            "suggested_replies": turn.suggested_replies,
                            "escalate": turn.escalate,
                            "follow_up_question": turn.follow_up_question,
                            "citations": turn.citations,
                            "response_source": turn.response_source,
                            "response_type": turn.response_type,
                            "flow_title": turn.flow_title,
                            "matched_flow_intent": turn.matched_flow_intent,
                            "intent_match_confidence": turn.intent_match_confidence,
                        },
                    }
                )
            finally:
                db.close()

    except WebSocketDisconnect:
        return
