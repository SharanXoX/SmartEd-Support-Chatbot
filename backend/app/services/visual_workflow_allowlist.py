"""Strict allowlist for screenshot / pictorial support-assets walkthroughs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.flow_registry import FlowMatch

# Only pre-approved workflows may return support_flow visual_steps.
ALLOWED_VISUAL_WORKFLOWS: frozenset[str] = frozenset({"password_reset"})

_INTENT_ALIASES: dict[str, str] = {
    "reset_password": "password_reset",
    "password_reset": "password_reset",
}


def normalize_visual_workflow_intent(intent: str | None) -> str | None:
    if not intent or not str(intent).strip():
        return None
    key = str(intent).strip().lower()
    return _INTENT_ALIASES.get(key, key)


def is_visual_workflow_allowed(intent: str | None) -> bool:
    normalized = normalize_visual_workflow_intent(intent)
    return bool(normalized and normalized in ALLOWED_VISUAL_WORKFLOWS)


def filter_visual_flow_match(flow_match: FlowMatch | None) -> FlowMatch | None:
    """Drop semantic flow matches that are not on the visual allowlist."""
    if flow_match is None:
        return None
    if is_visual_workflow_allowed(flow_match.flow.intent):
        return flow_match
    return None


def allowlist_prompt_block() -> str:
    allowed = ", ".join(sorted(ALLOWED_VISUAL_WORKFLOWS))
    return (
        "VISUAL_WORKFLOW_POLICY:\n"
        f"- ONLY these support-assets flows may use screenshot walkthroughs: {allowed}\n"
        "- Do NOT populate visual_steps in LLM JSON responses (walkthroughs are server-driven for allowed flows only).\n"
        "- For other how-to questions: short text + navigation_actions only, never invent screenshots."
    )
