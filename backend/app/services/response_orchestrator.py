"""Decide navigation-only vs walkthrough vs hybrid vs conversational responses."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum

from app.config import Settings
from app.services.conversation_context import ConversationContext, should_skip_bundled_flow
from app.services.feature_first_routing import evaluate_feature_first
from app.services.flow_registry import FlowMatch, match_support_flow
from app.services.navigation_registry import (
    LmsRoute,
    RouteMatch,
    match_navigation_route,
    route_for_flow,
)
from app.services.query_classifier import QueryClassification, classify_query
from app.services.route_context import normalize_route
from app.services.support_indexer import get_support_indexer
from app.services.visual_workflow_allowlist import (
    filter_visual_flow_match,
    is_visual_workflow_allowed,
)

logger = logging.getLogger("smarted.orchestrator")


class ResponseMode(str, Enum):
    NAVIGATE_ONLY = "navigate_only"
    WALKTHROUGH = "walkthrough"
    HYBRID = "hybrid"
    CONVERSATIONAL = "conversational"


@dataclass(frozen=True)
class OrchestratorPlan:
    mode: ResponseMode
    classification: QueryClassification
    route_match: RouteMatch | None
    flow_match: FlowMatch | None
    target_route: LmsRoute | None
    skip_bundled: bool = False
    feature_first_locked: bool = False
    on_page_contextual: bool = False


def _pick_target_route(
    route_match: RouteMatch | None,
    flow_match: FlowMatch | None,
) -> LmsRoute | None:
    if route_match:
        return route_match.route
    if flow_match:
        return route_for_flow(flow_match.flow.intent)
    return None


def _visual_flow(flow_match: FlowMatch | None) -> bool:
    return flow_match is not None and is_visual_workflow_allowed(flow_match.flow.intent)


def decide_response_mode(
    classification: QueryClassification,
    *,
    route_match: RouteMatch | None,
    flow_match: FlowMatch | None,
    current_route: str | None,
    message: str = "",
    feature_first_locked: bool = False,
    on_page_contextual: bool = False,
) -> ResponseMode:
    here = normalize_route(current_route)
    target = _pick_target_route(route_match, flow_match)
    target_path = normalize_route(target.path) if target else ""
    already_there = bool(target_path and target_path == here)
    lower = message.lower()
    visual = _visual_flow(flow_match)

    # Feature-first: LMS registry overrides generic conversational fallback.
    if feature_first_locked and route_match and not classification.is_how_to:
        return ResponseMode.NAVIGATE_ONLY

    # On courses page: "continue learning" — never auto-walkthrough unless password reset.
    if here == "/demo/courses" and re.search(
        r"\b(continue|which course|pick a course|start module)\b", lower
    ):
        if visual and (classification.is_how_to or classification.is_process_oriented):
            return ResponseMode.WALKTHROUGH
        return ResponseMode.CONVERSATIONAL

    if classification.intent_type == "informational_intent":
        if route_match and not classification.is_how_to and not already_there:
            if (
                classification.is_direct_navigation
                or route_match.confidence >= 0.5
                or on_page_contextual
            ):
                return ResponseMode.NAVIGATE_ONLY
        return ResponseMode.CONVERSATIONAL

    if classification.intent_type == "navigation_intent":
        if route_match or target:
            if already_there:
                return ResponseMode.NAVIGATE_ONLY if on_page_contextual else ResponseMode.CONVERSATIONAL
            if classification.is_how_to and visual:
                return ResponseMode.HYBRID
            return ResponseMode.NAVIGATE_ONLY
        return ResponseMode.CONVERSATIONAL

    if classification.intent_type in ("workflow_intent", "troubleshooting_intent", "onboarding_intent"):
        if visual:
            if target_path and not already_there and (
                classification.is_how_to or classification.is_process_oriented
            ):
                return ResponseMode.HYBRID
            return ResponseMode.WALKTHROUGH
        if route_match and not already_there:
            return ResponseMode.NAVIGATE_ONLY
        return ResponseMode.CONVERSATIONAL

    if visual:
        if classification.is_how_to or classification.is_process_oriented:
            if target_path and not already_there:
                return ResponseMode.HYBRID
            return ResponseMode.WALKTHROUGH
        if route_match and not already_there:
            return ResponseMode.NAVIGATE_ONLY

    if route_match and not already_there:
        return ResponseMode.NAVIGATE_ONLY

    return ResponseMode.CONVERSATIONAL


def plan_response(
    settings: Settings,
    message: str,
    current_route: str | None,
    ctx: ConversationContext,
) -> OrchestratorPlan:
    get_support_indexer().refresh(settings)
    classification = classify_query(message)
    route_match = match_navigation_route(message)
    raw_flow_match = match_support_flow(settings, message)
    flow_match = filter_visual_flow_match(raw_flow_match)

    ff = evaluate_feature_first(
        message,
        current_route,
        classification=classification,
        route_match=route_match,
    )
    if ff.route_match and (route_match is None or ff.route_match.confidence >= (route_match.confidence if route_match else 0)):
        route_match = ff.route_match

    skip = False
    if raw_flow_match and should_skip_bundled_flow(settings, message, ctx, raw_flow_match):
        skip = True
        flow_match = None

    if skip and not ff.lock_before_llm:
        mode = ResponseMode.CONVERSATIONAL
    else:
        mode = decide_response_mode(
            classification,
            route_match=route_match,
            flow_match=flow_match,
            current_route=current_route,
            message=message,
            feature_first_locked=ff.lock_before_llm,
            on_page_contextual=ff.on_page_contextual,
        )

    if ff.lock_before_llm and route_match:
        mode = ResponseMode.NAVIGATE_ONLY

    target = _pick_target_route(route_match, flow_match)

    if raw_flow_match and not flow_match and mode in (ResponseMode.WALKTHROUGH, ResponseMode.HYBRID):
        mode = (
            ResponseMode.NAVIGATE_ONLY
            if target and normalize_route(target.path) != normalize_route(current_route)
            else ResponseMode.CONVERSATIONAL
        )

    logger.info(
        "[ORCH] intent=%s mode=%s route=%s flow=%s ff_lock=%s on_page=%s here=%s",
        classification.intent_type,
        mode.value,
        target.path if target else None,
        flow_match.flow.intent if flow_match else None,
        ff.lock_before_llm,
        ff.on_page_contextual,
        normalize_route(current_route),
    )

    return OrchestratorPlan(
        mode=mode,
        classification=classification,
        route_match=route_match,
        flow_match=flow_match,
        target_route=target,
        skip_bundled=skip,
        feature_first_locked=ff.lock_before_llm,
        on_page_contextual=ff.on_page_contextual,
    )
