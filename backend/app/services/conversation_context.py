"""Session context for flow follow-ups and conversational continuity."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Conversation, Message
from app.services.flow_registry import FlowMatch, SupportFlowDefinition, list_flows, match_support_flow
from app.services.visual_workflow_allowlist import is_visual_workflow_allowed


@dataclass(frozen=True)
class ConversationContext:
    active_flow_intent: str | None
    last_response_source: str | None
    last_suggested_replies: tuple[str, ...]
    last_assistant_preview: str


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def get_conversation_context(db: Session, conversation_id: str) -> ConversationContext:
    last_assistant = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role == "assistant")
        .order_by(Message.created_at.desc())
        .first()
    )
    if not last_assistant:
        return ConversationContext(None, None, (), "")

    meta = last_assistant.meta or {}
    suggested = tuple(str(s) for s in (meta.get("suggested_replies") or [])[:8])
    active = meta.get("matched_flow_intent") or meta.get("intent")
    if meta.get("response_source") != "support_flow" and meta.get("response_source") != "llm":
        active = meta.get("matched_flow_intent")

    source = meta.get("response_source")
    if source == "support_flow":
        intent_candidate = meta.get("matched_flow_intent") or meta.get("intent") or active
        active = intent_candidate if is_visual_workflow_allowed(str(intent_candidate or "")) else None
    elif source == "llm" and meta.get("matched_flow_intent"):
        active = meta.get("matched_flow_intent")

    preview = (last_assistant.content or "")[:400]
    return ConversationContext(
        active_flow_intent=str(active) if active else None,
        last_response_source=str(source) if source else None,
        last_suggested_replies=suggested,
        last_assistant_preview=preview,
    )


def _matches_suggested_reply(message: str, suggested: tuple[str, ...]) -> bool:
    msg = _normalize(message)
    for chip in suggested:
        chip_n = _normalize(chip)
        if not chip_n:
            continue
        if msg == chip_n or chip_n in msg or msg in chip_n:
            return True
    return False


def _flow_by_intent(settings: Settings, intent: str) -> SupportFlowDefinition | None:
    for flow in list_flows(settings):
        if flow.intent == intent:
            return flow
    return None


def is_contextual_follow_up(
    settings: Settings,
    message: str,
    ctx: ConversationContext,
) -> bool:
    """True when the user is continuing an in-progress support topic (not starting a new flow)."""
    if not ctx.active_flow_intent:
        return False

    if _matches_suggested_reply(message, ctx.last_suggested_replies):
        return True

    if ctx.last_response_source == "support_flow" and is_visual_workflow_allowed(ctx.active_flow_intent):
        if _matches_suggested_reply(message, ctx.last_suggested_replies):
            return True
        new_match = match_support_flow(settings, message)
        if new_match and new_match.flow.intent != ctx.active_flow_intent:
            if new_match.confidence >= settings.intent_flow_threshold + 0.08:
                return False
        if len(message.split()) <= 14:
            return True

    return False


def should_skip_bundled_flow(
    settings: Settings,
    message: str,
    ctx: ConversationContext,
    flow_match: FlowMatch | None,
) -> bool:
    if is_contextual_follow_up(settings, message, ctx):
        return True
    if flow_match is None:
        return False
    if ctx.active_flow_intent and flow_match.flow.intent != ctx.active_flow_intent:
        if is_contextual_follow_up(settings, message, ctx):
            return True
    return False


def build_flow_context_prompt(settings: Settings, ctx: ConversationContext) -> str:
    if not ctx.active_flow_intent or not is_visual_workflow_allowed(ctx.active_flow_intent):
        return ""
    flow = _flow_by_intent(settings, ctx.active_flow_intent)
    lines = [
        f"ACTIVE_SUPPORT_TOPIC: {ctx.active_flow_intent}",
        "The user is continuing a support conversation after guided steps or prior answers.",
        "Answer their follow-up directly; do not repeat the full step-by-step walkthrough unless they ask.",
    ]
    if flow and flow.intro:
        lines.append(f"Topic intro was: {flow.intro}")
    if ctx.last_assistant_preview:
        lines.append(f"Your last reply began with: {ctx.last_assistant_preview[:280]}")
    if flow and flow.suggested_replies:
        lines.append("Suggested chips shown to user: " + ", ".join(flow.suggested_replies))
    return "\n".join(lines)
