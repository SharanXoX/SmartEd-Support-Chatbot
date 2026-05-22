"""Classify student queries before choosing navigation vs walkthrough vs chat."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

IntentType = Literal[
    "navigation_intent",
    "workflow_intent",
    "informational_intent",
    "troubleshooting_intent",
    "onboarding_intent",
]

HOW_TO_RE = re.compile(
    r"\b("
    r"how\s+(?:do|can|to|would|should)|"
    r"where\s+(?:do|can|to)\s+i|"
    r"help\s+me\s+(?:to\s+)?|"
    r"steps?\s+to|"
    r"walk\s+me\s+through|"
    r"guide\s+me|"
    r"show\s+me\s+how"
    r")\b",
    re.I,
)
NAV_DIRECT_RE = re.compile(
    r"\b("
    r"open|go\s+to|take\s+me|navigate|bring\s+me|visit|"
    r"view\s+my|see\s+my|show\s+my|show\s+me\s+my|check\s+my|find\s+my|"
    r"where\s+(?:is|are)\s+my|get\s+to|display\s+my|look\s+at\s+my"
    r")\b",
    re.I,
)
PAGE_LOOKUP_RE = re.compile(
    r"\b(check|show|view|see|open|find|display|go\s+to)\s+(?:my\s+)?\w+",
    re.I,
)
WORKFLOW_RE = re.compile(
    r"\b("
    r"submit|upload|complete|finish|download|enroll|register|watch|reset|"
    r"fix|solve|cannot|can't|failed|error|stuck|locked"
    r")\b",
    re.I,
)
POLICY_RE = re.compile(
    r"\b("
    r"what\s+is|what's|policy|refund|grading|attendance|terms|rules"
    r")\b",
    re.I,
)
ONBOARDING_RE = re.compile(
    r"\b(first\s+time|new\s+student|getting\s+started|begin|start\s+here)\b",
    re.I,
)


@dataclass(frozen=True)
class QueryClassification:
    intent_type: IntentType
    is_how_to: bool
    is_direct_navigation: bool
    is_policy_style: bool
    is_process_oriented: bool


def classify_query(message: str) -> QueryClassification:
    msg = message.strip()
    lower = msg.lower()

    is_how_to = bool(HOW_TO_RE.search(msg))
    is_direct_nav = (bool(NAV_DIRECT_RE.search(msg)) or bool(PAGE_LOOKUP_RE.search(msg))) and not is_how_to
    is_policy = bool(POLICY_RE.search(msg)) and not is_how_to and not WORKFLOW_RE.search(msg)
    is_process = bool(WORKFLOW_RE.search(msg))
    is_onboarding = bool(ONBOARDING_RE.search(msg))

    if is_policy:
        intent: IntentType = "informational_intent"
    elif is_onboarding:
        intent = "onboarding_intent"
    elif is_how_to or (is_process and not is_direct_nav):
        if re.search(r"\b(fix|failed|error|cannot|can't|stuck|locked|not\s+working)\b", lower):
            intent = "troubleshooting_intent"
        else:
            intent = "workflow_intent"
    elif is_direct_nav:
        intent = "navigation_intent"
    elif is_process:
        intent = "workflow_intent"
    else:
        intent = "informational_intent"

    return QueryClassification(
        intent_type=intent,
        is_how_to=is_how_to,
        is_direct_navigation=is_direct_nav,
        is_policy_style=is_policy,
        is_process_oriented=is_process,
    )
