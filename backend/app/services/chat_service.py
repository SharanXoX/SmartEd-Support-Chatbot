"""Intent-aware flows + provider-backed LLM replies (Groq default, OpenAI optional)."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ai.provider_factory import ProviderSelection, get_chat_provider
from app.config import Settings
from app.models import Conversation, FAQ, Message, VisualGuide
from app.schemas import ChatTurnResponse, NavigationAction, VisualStep
from app.services import escalation_service, rag_service
from app.services.conversation_context import (
    build_flow_context_prompt,
    get_conversation_context,
    is_contextual_follow_up,
    should_skip_bundled_flow,
)
from app.services.asset_urls import enrich_visual_step_urls, get_public_base_url, resolve_step_image_url
from app.services.flow_registry import FlowMatch
from app.services.feature_guard import detect_unavailable_feature, unavailable_feature_reply
from app.services.context_sanitizer import filter_active_exams
from app.services.lms_context_service import build_lms_context_prompt, merge_client_lms_context
from app.services.query_context_resolver import (
    build_deterministic_chat_response,
    resolve_query_context,
    should_apply_deterministic_response,
)
from app.services.lms_feature_registry import registry_prompt_block
from app.services.navigation_registry import LmsRoute, registry_as_prompt_block
from app.services.response_orchestrator import OrchestratorPlan, ResponseMode, plan_response
from app.services.route_context import build_route_context_prompt, normalize_route
from app.services.student_context import build_student_context_prompt, personalization_hint
from app.services.support_indexer import get_support_indexer
from app.services.feature_first_routing import on_page_reply_for_route
from app.services.visual_workflow_allowlist import (
    allowlist_prompt_block,
    filter_visual_flow_match,
    is_visual_workflow_allowed,
)

logger = logging.getLogger("smarted.chat")

USER_FACING_AI_UNAVAILABLE = (
    "I'm having trouble accessing advanced AI support right now, but I can still help "
    "with guided troubleshooting. Try asking about password reset, payments, or uploads."
)

FLOW_FOLLOWUP_HINTS: dict[str, dict[str, str]] = {
    "password_reset": {
        "email": (
            "Check your spam or junk folder first. Confirm you're using the email on your account, "
            "wait a few minutes, then use **Forgot password** again to resend. If it still doesn't arrive, "
            "contact support with your registered email so we can verify the account."
        ),
        "locked": (
            "If you're still locked out after resetting, clear browser cache or try another browser. "
            "Make sure the new password meets requirements (8+ characters). I can escalate to a human agent if needed."
        ),
    },
}


SYSTEM_PROMPT = """You are a friendly student support coach inside an E-Learning platform (demo LMS).
Behaviors:
- Be concise, calm, and beginner-friendly.
- Prefer short numbered steps over long prose.
- Use LMS_CURRENT_PAGE when provided: do not send users to a page they are already on unless a sub-step is needed.
- When navigation helps, add navigation_actions (1-3 items) with {label, path} using demo paths like /demo/courses, /demo/assignments, /demo/dashboard.
- NEVER populate visual_steps in your JSON (screenshot walkthroughs are server-controlled for password reset only).
- If you lack verified information from CONTEXT or general product-safe defaults, ask a clarifying follow_up_question instead of guessing.
- Classify intent into one of: account, billing, technical, product_guidance, faq_general, complaint.
- confidence is your certainty about resolving without human help (0-1).
- Set escalate=false unless the user explicitly asks for a human (support handles escalation separately).
- suggested_replies: 2-4 short chips the user might tap next.

Respond ONLY as JSON matching keys:
reply (string),
intent (string),
confidence (number),
follow_up_question (string|null),
visual_steps (array of {step:int,title:string,description:string,image_url:string|null,open_url:string|null,auto_navigate:boolean,annotations:array}),
navigation_actions (array of {label:string,path:string}),
suggested_replies (array of string),
escalate (boolean),
citations (array of {title:string,snippet:string})

Annotations objects: {kind:string circle|arrow|highlight|label, x:number 0-1, y:number 0-1, w:number, h:number, label:string|null}
open_url should be a demo LMS path like /demo/courses when guiding navigation.
image_url should be a relative URL path like /demo-assets/... or /uploads/visuals/example.png when applicable, else null.
"""


def _faq_snippets(db: Session, query: str, limit: int = 5) -> str:
    q = f"%{query[:120]}%"
    rows = (
        db.query(FAQ).filter(FAQ.question.ilike(q) | FAQ.answer.ilike(q)).limit(limit).all()
    )
    if not rows:
        rows = db.query(FAQ).limit(limit).all()
    parts = []
    for r in rows:
        parts.append(f"FAQ: {r.question}\n{r.answer}")
    return "\n---\n".join(parts)


def _visual_catalog(db: Session) -> str:
    guides = db.query(VisualGuide).order_by(VisualGuide.created_at.desc()).limit(40).all()
    if not guides:
        return "(no screenshots indexed)"
    lines = []
    for g in guides:
        lines.append(f"- {g.title}: url=/uploads/visuals/{g.image_path.split('/')[-1]} tags={g.tags or ''}")
    return "\n".join(lines)


def _history(db: Session, conversation_id: str, max_turns: int = 12) -> list[dict[str, str]]:
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    trimmed = msgs[-max_turns:] if len(msgs) > max_turns else msgs
    return [{"role": m.role, "content": m.content} for m in trimmed]


def _static_flow_followup_reply(intent: str, message: str) -> str | None:
    hints = FLOW_FOLLOWUP_HINTS.get(intent)
    if not hints:
        return None
    msg = message.lower()
    if "email" in msg or "didn't get" in msg or "did not get" in msg or "spam" in msg:
        return hints.get("email")
    if "locked" in msg or "still" in msg or "not working" in msg:
        return hints.get("locked")
    return None


def _persist_exchange(
    db: Session,
    *,
    conversation: Conversation,
    user_message: str,
    reply: ChatTurnResponse,
    extra_meta: dict[str, Any] | None = None,
) -> None:
    assistant_meta: dict[str, Any] = {
        "intent": reply.intent,
        "confidence": reply.confidence,
        "visual_steps": [vs.model_dump() for vs in reply.visual_steps],
        "suggested_replies": reply.suggested_replies,
        "escalate": reply.escalate,
        "citations": reply.citations,
        "response_source": reply.response_source,
        "response_type": reply.response_type,
        "response_mode": reply.response_mode,
        "flow_title": reply.flow_title,
        "matched_flow_intent": reply.matched_flow_intent,
        "intent_match_confidence": reply.intent_match_confidence,
    }
    if extra_meta:
        assistant_meta.update(extra_meta)

    conversation.updated_at = datetime.utcnow()

    db.add(Message(conversation_id=conversation.id, role="user", content=user_message))
    db.add(
        Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply.reply,
            meta=assistant_meta,
        ),
    )
    db.commit()


def _user_nav_reply(
    *,
    settings: Settings,
    target_route_id: str,
    target_label: str,
    on_page: bool,
    lms_context: dict[str, Any] | None,
    user_message: str | None = None,
    current_route: str | None = None,
) -> str:
    merged = (
        merge_client_lms_context(
            lms_context,
            user_message=user_message,
            current_route=current_route,
        )
        if lms_context
        else {}
    )
    active = merged.get("activeUser") or merged.get("active_user") or {}
    courses = merged.get("courses") or active.get("courses") or []
    purchases = merged.get("purchases") or active.get("purchases") or []
    certs = active.get("certificates") or merged.get("certificates_count", 0)
    cert_n = len(certs) if isinstance(certs, list) else int(merged.get("certificates_count") or 0)
    name = active.get("name") or (merged.get("student") or {}).get("name") or "there"

    if on_page:
        reply = on_page_reply_for_route(target_route_id, target_label)
    else:
        reply = f"Opening **{target_label}** for you."

    if target_route_id == "certifications":
        if cert_n == 0:
            reply = (
                "You don't have any certificates yet. "
                "Complete a course (100% progress) to unlock certificates — they'll appear on **Certifications**."
            )
            if not on_page:
                reply = f"{reply}\n\nOpening **Certifications** for you."
        elif not on_page:
            reply = (
                f"{reply}\n\nYou have **{cert_n}** certificate(s) on your account."
            )
    elif target_route_id == "courses":
        active_courses = merged.get("active_courses") or []
        if len(courses) == 0:
            reply = (
                f"Hi {name} — you haven't enrolled in any courses yet. "
                "Browse the catalog or ask how to enroll in your first course."
            )
            if not on_page:
                reply = f"{reply}\n\nOpening **My Courses** for you."
        elif not on_page:
            reply = f"{reply}\n\nYou have **{len(active_courses) or len(courses)}** active course(s)."
    elif target_route_id == "exams":
        exams = filter_active_exams(
            merged.get("active_exams")
            or active.get("upcomingExams")
            or merged.get("upcoming_exams")
            or []
        )
        if exams:
            lines = [f"• **{e.get('title')}** — {e.get('date')}" for e in exams if isinstance(e, dict)]
            reply = "Your upcoming exams:\n" + "\n".join(lines)
            if not on_page:
                reply = f"{reply}\n\nOpening **Exams** for you."
        elif not on_page:
            reply = "You don't have any scheduled exams right now.\n\nOpening **Exams** for you."
        else:
            reply = on_page_reply_for_route(target_route_id, target_label)
    elif target_route_id == "purchases":
        if len(purchases) == 0:
            reply = "You don't have any purchases on your account yet."
            if not on_page:
                reply = f"{reply} Opening **My Purchases** to review order history."
        elif not on_page:
            reply = f"{reply}\n\nYou have **{len(purchases)}** purchase(s) on record."

    if not on_page and target_route_id not in ("certifications", "courses", "exams", "purchases"):
        hint = personalization_hint(
            settings,
            merged.get("student_id") or active.get("id"),
            user_message=user_message,
            current_route=current_route,
            lms_context=merged,
        )
        if hint:
            reply = f"{reply}\n\n{hint}"

    return reply


def _build_navigation_only_response(
    *,
    settings: Settings,
    plan: OrchestratorPlan,
    current_route: str | None,
    flow_match: FlowMatch | None = None,
    lms_context: dict[str, Any] | None = None,
    user_message: str | None = None,
) -> ChatTurnResponse:
    target = plan.target_route
    if not target:
        return ChatTurnResponse(
            reply="I can help you find that section — which area do you need: courses, assignments, or progress?",
            intent="navigation",
            confidence=0.5,
            response_source="navigation",
            response_type="navigation",
            response_mode=ResponseMode.NAVIGATE_ONLY.value,
        )

    here = normalize_route(current_route)
    path = normalize_route(target.path)
    on_page = path == here

    reply = _user_nav_reply(
        settings=settings,
        target_route_id=target.route_id,
        target_label=target.label,
        on_page=on_page,
        lms_context=lms_context,
        user_message=user_message,
        current_route=current_route,
    )

    intent = flow_match.flow.intent if flow_match else target.route_id
    confidence = float(flow_match.confidence) if flow_match else (plan.route_match.confidence if plan.route_match else 0.85)

    nav_actions: list[NavigationAction] = []
    if not on_page:
        nav_actions = [NavigationAction(label=f"Open {target.label}", path=path or target.path)]

    return ChatTurnResponse(
        reply=reply,
        intent=intent,
        confidence=confidence,
        visual_steps=[],
        suggested_replies=[
            f"How do I use {target.label}?",
            "I need human help",
        ],
        escalate=False,
        citations=[],
        response_source="navigation",
        response_type="navigation",
        response_mode=ResponseMode.NAVIGATE_ONLY.value,
        flow_title=target.label,
        matched_flow_intent=flow_match.flow.intent if flow_match else target.route_id,
        intent_match_confidence=confidence,
        navigation_actions=nav_actions,
    )


def _try_bundled_flow(
    db: Session,
    *,
    settings: Settings,
    conversation: Conversation,
    user_message: str,
    ctx,
    base_url: str = "",
    flow_match: FlowMatch | None = None,
    mode: ResponseMode = ResponseMode.HYBRID,
    current_route: str | None = None,
    target_route: LmsRoute | None = None,
) -> ChatTurnResponse | None:
    if flow_match is None:
        get_support_indexer().refresh(settings)
        flow_match = match_support_flow(settings, user_message)
    flow_match = filter_visual_flow_match(flow_match)
    if flow_match is None:
        return None
    if not is_visual_workflow_allowed(flow_match.flow.intent):
        return None
    if should_skip_bundled_flow(settings, user_message, ctx, flow_match):
        logger.info(
            "[FLOW] Skipping adaptive walkthrough %s — contextual follow-up (active=%s)",
            flow_match.flow.intent,
            ctx.active_flow_intent,
        )
        return None

    logger.info(
        "[FLOW] mode=%s match %s confidence=%.3f scores=%s",
        mode.value,
        flow_match.flow.intent,
        flow_match.confidence,
        getattr(flow_match, "scores", {}),
    )

    flow = flow_match.flow
    here = normalize_route(current_route)
    total = len(flow.steps)
    visual_steps: list[VisualStep] = []

    for i, step in enumerate(flow.steps, start=1):
        title = f"Step {i} of {total}"
        img = resolve_step_image_url(
            settings,
            flow_id=flow.intent,
            image_ref=step.image,
        )
        step_path = normalize_route(step.open_url)
        auto_nav = bool(step.auto_navigate)
        if mode == ResponseMode.WALKTHROUGH:
            auto_nav = False
        elif mode == ResponseMode.HYBRID:
            auto_nav = auto_nav and i == 1 and bool(step_path) and step_path != here

        visual_steps.append(
            VisualStep(
                step=i,
                title=title,
                description=step.text,
                image_url=img,
                open_url=step.open_url,
                auto_navigate=auto_nav,
                annotations=[],
            ),
        )

    suggested = flow.suggested_replies[:6] if flow.suggested_replies else [
        "Show me account settings help",
        "It didn't work — what's next?",
    ]

    enriched_steps = enrich_visual_step_urls(settings, visual_steps, base_url=base_url)
    title = flow.title or flow.intent.replace("_", " ").title()
    if mode == ResponseMode.HYBRID and target_route and normalize_route(target_route.path) != here:
        intro = f"I'll open **{target_route.label}** and walk you through the steps."
    else:
        intro = (flow.intro or f"Here's a guided walkthrough for **{title}**.").strip()
    hint = personalization_hint(settings)
    if hint and mode != ResponseMode.HYBRID:
        intro = f"{intro}\n\n{hint}"
    elif hint and mode == ResponseMode.HYBRID:
        intro = f"{intro}\n\n{hint}"
    nav_actions: list[NavigationAction] = []
    seen_paths: set[str] = set()
    for vs in enriched_steps:
        path = normalize_route(vs.open_url)
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        label = path.rsplit("/", 1)[-1].replace("-", " ").title() or "Open page"
        nav_actions.append(NavigationAction(label=f"Open {label}", path=path))
        if len(nav_actions) >= 3:
            break
    reply = ChatTurnResponse(
        reply=intro,
        intent=flow.intent,
        confidence=float(flow_match.confidence),
        visual_steps=enriched_steps,
        suggested_replies=suggested,
        escalate=False,
        follow_up_question=None,
        citations=[],
        response_source="support_flow",
        response_type="support_flow",
        response_mode=mode.value,
        flow_title=title,
        matched_flow_intent=flow.intent,
        intent_match_confidence=float(flow_match.confidence),
        navigation_actions=nav_actions,
    )

    _persist_exchange(
        db,
        conversation=conversation,
        user_message=user_message,
        reply=reply,
        extra_meta={
            "match_scores": getattr(flow_match, "scores", {}),
            "response_mode": mode.value,
        },
    )
    return reply


def _build_llm_messages(
    db: Session,
    *,
    settings: Settings,
    conversation: Conversation,
    user_message: str,
    ctx,
    selection: ProviderSelection,
    current_route: str | None = None,
    lms_context: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    rag_hits = rag_service.retrieve_context(settings, user_message, k=6)
    rag_blob = "\n---\n".join(h["content"] for h in rag_hits[:6])
    faq_blob = _faq_snippets(db, user_message)
    visuals = _visual_catalog(db)

    flow_context = build_flow_context_prompt(settings, ctx)
    follow_up = is_contextual_follow_up(settings, user_message, ctx)

    merged_ctx = merge_client_lms_context(
        lms_context,
        user_message=user_message,
        current_route=current_route,
    )
    query_resolution = resolve_query_context(
        user_message,
        merged_ctx,
        current_route=current_route,
    )
    student_id = merged_ctx.get("student_id")
    if not student_id and merged_ctx.get("student") and isinstance(merged_ctx["student"], dict):
        student_id = merged_ctx["student"].get("student_id")
    route_block = build_route_context_prompt(current_route)
    scoped_block = query_resolution.minimal_prompt
    use_scoped = bool(
        scoped_block
        and query_resolution.category.value not in ("navigation_query", "workflow_query")
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    if use_scoped:
        messages.append({"role": "system", "content": scoped_block})
        messages.append(
            {
                "role": "system",
                "content": (
                    "Use QUERY_SCOPED_CONTEXT only. Format a natural, concise reply. "
                    "Do not invent courses, exams, or dates outside that block."
                ),
            },
        )
    else:
        student_block = build_student_context_prompt(
            settings, student_id, merged_ctx, user_message=user_message
        )
        lms_block = build_lms_context_prompt(merged_ctx, user_message=user_message)
        if student_block:
            messages.append({"role": "system", "content": student_block})
        if lms_block:
            messages.append({"role": "system", "content": lms_block})
    if route_block:
        messages.append({"role": "system", "content": route_block})
    messages.append({"role": "system", "content": registry_as_prompt_block()})
    messages.append({"role": "system", "content": registry_prompt_block()})
    messages.append({"role": "system", "content": allowlist_prompt_block()})
    messages.append(
        {
            "role": "system",
            "content": (
                "Response strategy: Use navigation_actions for simple 'open/go to' requests. "
                "Never include visual_steps in JSON. For how-to questions without an approved server walkthrough, "
                "give concise text steps and optional navigation_actions only."
            ),
        }
    )
    messages.extend(
        [
        {
            "role": "system",
            "content": "CONTEXT from retrieval:\n" + rag_blob[:12000],
        },
        {"role": "system", "content": "FAQ BANK:\n" + faq_blob[:6000]},
        {"role": "system", "content": "VISUAL LIBRARY:\n" + visuals[:4000]},
        ]
    )
    if flow_context:
        messages.append({"role": "system", "content": flow_context})
        logger.info("[AI] Contextual follow-up for topic=%s", ctx.active_flow_intent)
    if follow_up:
        messages.append(
            {
                "role": "system",
                "content": (
                    "The user's message is a FOLLOW-UP to the previous support topic. "
                    "Answer specifically what they asked (e.g. missing email, still locked out). "
                    "Do not restart the full tutorial unless they ask."
                ),
            },
        )

    history = _history(db, conversation.id)
    messages.extend(history)
    if not history or history[-1].get("content") != user_message:
        messages.append({"role": "user", "content": user_message})

    return messages


def _provider_unavailable_reply(
    db: Session,
    *,
    conversation: Conversation,
    user_message: str,
    ctx,
    selection: ProviderSelection,
) -> ChatTurnResponse:
    static = None
    if ctx.active_flow_intent:
        static = _static_flow_followup_reply(ctx.active_flow_intent, user_message)

    reply_text = static or USER_FACING_AI_UNAVAILABLE
    suggested = list(ctx.last_suggested_replies)[:4] if ctx.last_suggested_replies else [
        "How do I reset my password?",
        "Payment failed",
    ]

    reply = ChatTurnResponse(
        reply=reply_text,
        intent=ctx.active_flow_intent or "technical",
        confidence=0.4 if static else 0.2,
        escalate=False,
        suggested_replies=suggested,
        response_source="fallback",
        matched_flow_intent=ctx.active_flow_intent,
    )

    _persist_exchange(
        db,
        conversation=conversation,
        user_message=user_message,
        reply=reply,
        extra_meta={"provider_error": selection.error_detail, "effective_provider": None},
    )
    logger.warning("[AI] Fallback response (no provider): %s", selection.error_detail)
    return reply


def _parse_llm_payload(data: dict[str, Any], rag_hits: list) -> ChatTurnResponse:
    # LLM must not emit screenshot walkthroughs — only allowlisted server flows do.
    visual_steps: list[VisualStep] = []

    nav_raw = data.get("navigation_actions") or []
    navigation_actions: list[NavigationAction] = []
    for item in nav_raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        path = normalize_route(str(item.get("path") or ""))
        if label and path:
            navigation_actions.append(NavigationAction(label=label, path=path))

    reply = ChatTurnResponse(
        reply=str(data.get("reply") or "").strip() or "How else can I help?",
        intent=str(data.get("intent") or "faq_general"),
        confidence=float(data.get("confidence") or 0.5),
        follow_up_question=data.get("follow_up_question"),
        visual_steps=visual_steps,
        suggested_replies=list(data.get("suggested_replies") or [])[:6],
        escalate=bool(data.get("escalate")),
        citations=list(data.get("citations") or [])[:8],
        response_source="llm",
        matched_flow_intent=data.get("matched_flow_intent"),
        intent_match_confidence=None,
        navigation_actions=navigation_actions[:4],
    )

    citations_from_rag = [
        {"title": str(h.get("metadata", {}).get("source", "doc")), "snippet": h["content"][:280]}
        for h in rag_hits[:3]
    ]
    if not reply.citations:
        reply.citations = citations_from_rag
    return reply


def generate_turn(
    db: Session,
    *,
    settings: Settings,
    conversation: Conversation,
    user_message: str,
    base_url: str = "",
    current_route: str | None = None,
    lms_context: dict[str, Any] | None = None,
) -> ChatTurnResponse:
    ctx = get_conversation_context(db, conversation.id)
    effective_base = base_url

    unavailable = detect_unavailable_feature(user_message)
    if unavailable:
        blocked = ChatTurnResponse(
            reply=unavailable_feature_reply(unavailable),
            intent="unavailable_feature",
            confidence=0.95,
            visual_steps=[],
            suggested_replies=["Open my courses", "View exams", "Contact support"],
            escalate=False,
            citations=[],
            response_source="fallback",
            response_type="llm",
            response_mode=ResponseMode.CONVERSATIONAL.value,
            matched_flow_intent=unavailable.feature_key,
        )
        _persist_exchange(
            db,
            conversation=conversation,
            user_message=user_message,
            reply=blocked,
            extra_meta={"unavailable_feature": unavailable.feature_key},
        )
        return blocked

    lms_enriched = merge_client_lms_context(
        lms_context,
        user_message=user_message,
        current_route=current_route,
    )
    query_resolution = resolve_query_context(
        user_message,
        lms_enriched,
        current_route=current_route,
    )
    lms_enriched["query_resolution"] = {
        "category": query_resolution.category.value,
        "outcome": query_resolution.outcome.value,
        "entity_matched": query_resolution.entity_matched,
    }

    orch_plan = plan_response(settings, user_message, current_route, ctx)

    if should_apply_deterministic_response(
        query_resolution,
        orchestrator_mode=orch_plan.mode.value,
    ):
        det = build_deterministic_chat_response(
            query_resolution,
            current_route=current_route,
        )
        det_reply = ChatTurnResponse(
            reply=det["reply"],
            intent=det["intent"],
            confidence=det["confidence"],
            visual_steps=[],
            suggested_replies=["View exams", "My courses", "Contact support"],
            escalate=False,
            citations=[],
            response_source=det["response_source"],
            response_type=det["response_type"],
            response_mode=det["response_mode"],
            navigation_actions=det["navigation_actions"],
        )
        _persist_exchange(
            db,
            conversation=conversation,
            user_message=user_message,
            reply=det_reply,
            extra_meta={
                "response_mode": det["response_mode"],
                "query_category": query_resolution.category.value,
                "query_outcome": query_resolution.outcome.value,
                "entity_course_id": query_resolution.entity.course_id if query_resolution.entity else None,
            },
        )
        return det_reply

    if orch_plan.mode == ResponseMode.NAVIGATE_ONLY and orch_plan.target_route:
        nav_reply = _build_navigation_only_response(
            settings=settings,
            plan=orch_plan,
            current_route=current_route,
            flow_match=orch_plan.flow_match,
            lms_context=lms_enriched,
            user_message=user_message,
        )
        _persist_exchange(
            db,
            conversation=conversation,
            user_message=user_message,
            reply=nav_reply,
            extra_meta={
                "response_mode": orch_plan.mode.value,
                "intent_type": orch_plan.classification.intent_type,
            },
        )
        return nav_reply

    if (
        orch_plan.mode in (ResponseMode.WALKTHROUGH, ResponseMode.HYBRID)
        and orch_plan.flow_match
        and is_visual_workflow_allowed(orch_plan.flow_match.flow.intent)
    ):
        vf = _try_bundled_flow(
            db,
            settings=settings,
            conversation=conversation,
            user_message=user_message,
            ctx=ctx,
            base_url=effective_base,
            flow_match=orch_plan.flow_match,
            mode=orch_plan.mode,
            current_route=current_route,
            target_route=orch_plan.target_route,
        )
        if vf is not None:
            return vf

    selection = get_chat_provider(settings)
    if selection.provider is None:
        return _provider_unavailable_reply(
            db,
            conversation=conversation,
            user_message=user_message,
            ctx=ctx,
            selection=selection,
        )

    messages = _build_llm_messages(
        db,
        settings=settings,
        conversation=conversation,
        user_message=user_message,
        ctx=ctx,
        selection=selection,
        current_route=current_route,
        lms_context=lms_enriched,
    )
    rag_hits = rag_service.retrieve_context(settings, user_message, k=6)

    try:
        data: dict[str, Any] = selection.provider.complete_json(messages=messages, temperature=0.4)
    except RuntimeError as exc:
        logger.exception("[AI] Provider call failed: %s", exc)
        static = _static_flow_followup_reply(ctx.active_flow_intent or "", user_message)
        reply = ChatTurnResponse(
            reply=str(exc) if static is None else static,
            intent=ctx.active_flow_intent or "technical",
            confidence=0.35,
            escalate=False,
            suggested_replies=list(ctx.last_suggested_replies)[:4] or ["Try again", "Contact support"],
            response_source="fallback",
            matched_flow_intent=ctx.active_flow_intent,
        )
        _persist_exchange(
            db,
            conversation=conversation,
            user_message=user_message,
            reply=reply,
            extra_meta={
                "provider_error": str(exc),
                "effective_provider": selection.effective_provider,
            },
        )
        return reply
    except Exception as exc:
        logger.exception("[AI] Unexpected provider error: %s", exc)
        return _provider_unavailable_reply(
            db,
            conversation=conversation,
            user_message=user_message,
            ctx=ctx,
            selection=selection,
        )

    reply = _parse_llm_payload(data, rag_hits)
    if ctx.active_flow_intent and not reply.matched_flow_intent:
        if is_visual_workflow_allowed(ctx.active_flow_intent):
            reply.matched_flow_intent = ctx.active_flow_intent
    if reply.visual_steps and not is_visual_workflow_allowed(reply.matched_flow_intent):
        reply = reply.model_copy(update={"visual_steps": []})
    if reply.visual_steps:
        reply = reply.model_copy(
            update={
                "visual_steps": enrich_visual_step_urls(
                    settings, reply.visual_steps, base_url=effective_base
                )
            }
        )

    should_escalate = reply.escalate or reply.confidence < 0.35
    if should_escalate:
        recent = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .all()
        )[-40:]
        escalation_service.create_ticket(
            db,
            settings=settings,
            conversation_id=conversation.id,
            reason=f"Escalated intent={reply.intent} conf={reply.confidence}",
            transcript=[{"role": m.role, "content": m.content} for m in recent]
            + [{"role": "user", "content": user_message}],
            confidence=reply.confidence,
        )

    _persist_exchange(
        db,
        conversation=conversation,
        user_message=user_message,
        reply=reply,
        extra_meta={"effective_provider": selection.effective_provider},
    )
    logger.info(
        "[AI] LLM turn complete provider=%s intent=%s",
        selection.effective_provider,
        reply.intent,
    )
    return reply


def stream_reply_chunks(reply_text: str, chunk_size: int = 24) -> list[str]:
    """Split assistant reply into chunks for websocket streaming."""

    reply_text = reply_text.strip()
    if not reply_text:
        return [""]
    chunks: list[str] = []
    buf = ""
    for token in re.split(r"(\s+)", reply_text):
        buf += token
        if len(buf) >= chunk_size:
            chunks.append(buf)
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks
