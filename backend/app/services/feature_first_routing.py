"""Feature-first routing: LMS registry wins over generic LLM guidance."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.navigation_registry import RouteMatch, match_navigation_route
from app.services.query_classifier import QueryClassification, classify_query
from app.services.route_context import normalize_route

# View/list questions about LMS sections (not policy definitions).
FEATURE_LOOKUP_RE = re.compile(
    r"\b("
    r"what|which|where\s+are|where\s+is|where\s+can\s+i\s+(?:find|see)|"
    r"list|show|tell\s+me|display|have\s+i|did\s+i|bought|enrolled|"
    r"my\s+\w+\s+(?:are|is|list)"
    r")\b",
    re.I,
)

# Strong coupling between inquiry verbs and LMS nouns.
FEATURE_NOUN_RE = re.compile(
    r"\b("
    r"purchases?|orders?|payments?|billing|bought|"
    r"courses?|enrolled|enrollments?|"
    r"exams?|tests?|assessments?|"
    r"certificates?|certifications?|"
    r"profile|account|email|"
    r"announcements?|calendar|schedule|"
    r"assignments?|homework|grades?|progress|scores?"
    r")\b",
    re.I,
)

POLICY_DEFINITION_RE = re.compile(
    r"\b(what\s+is\s+the|what's\s+the|explain\s+the|define)\s+(\w+\s+)?(policy|rule|refund)\b",
    re.I,
)

ON_PAGE_CONTEXT: dict[str, str] = {
    "purchases": (
        "Your **purchases** are listed on this page — each card shows the course you bought, "
        "the purchase date, and the price. Scroll the list to review your order history."
    ),
    "courses": (
        "Your **enrolled courses** are shown here with progress and the next module. "
        "Use **Continue** on any course to pick up where you left off."
    ),
    "exams": (
        "Your **upcoming and completed exams** are listed here with dates and status. "
        "Check each row for the course and scheduled time."
    ),
    "certifications": (
        "Your **certificates** appear here after you complete a course (100% progress). "
        "If none are shown yet, finish all modules in a course to unlock one."
    ),
    "profile": (
        "Your **profile and learning stats** are on this page — account details, enrolled course count, "
        "and recent activity."
    ),
    "dashboard": "Your **dashboard** summarizes continue learning, due work, and progress across courses.",
    "announcements": "Platform **announcements** from instructors appear here when available.",
    "calendar": "Your learning **calendar** and key dates are shown on this page.",
    "settings": "Account **settings** — theme, notifications, and password options — are on this page.",
    "help": "**Help & support** resources, FAQ topics, and contact options are available here.",
    "assignments": "Your **assignments** and due dates are listed on this page.",
}


@dataclass(frozen=True)
class FeatureFirstDecision:
    """Result of deterministic feature-first evaluation."""

    route_match: RouteMatch | None
    force_navigation_response: bool
    on_page_contextual: bool
    lock_before_llm: bool


def is_feature_lookup_query(message: str, *, classification: QueryClassification | None = None) -> bool:
    """True when the user is asking to view/list LMS data (not policy or how-to)."""
    msg = message.strip()
    if not msg:
        return False
    if classification and classification.is_how_to:
        return False
    if POLICY_DEFINITION_RE.search(msg):
        return False
    if FEATURE_LOOKUP_RE.search(msg) and FEATURE_NOUN_RE.search(msg):
        return True
    # "what purchases have I done", "courses did I buy"
    if re.search(r"\bwhat\b.*\b(purchases?|courses?|exams?)\b", msg, re.I):
        return True
    if re.search(r"\b(purchases?|courses?)\b.*\b(bought|done|have\s+i)\b", msg, re.I):
        return True
    return False


def evaluate_feature_first(
    message: str,
    current_route: str | None,
    *,
    classification: QueryClassification | None = None,
    route_match: RouteMatch | None = None,
) -> FeatureFirstDecision:
    """
    LMS registry is primary source of truth.
    Lock navigation / on-page contextual replies before LLM fallback.
    """
    classification = classification or classify_query(message)
    route_match = route_match or match_navigation_route(message)
    here = normalize_route(current_route)

    if not route_match or classification.is_how_to:
        return FeatureFirstDecision(
            route_match=route_match,
            force_navigation_response=False,
            on_page_contextual=False,
            lock_before_llm=False,
        )

    target_path = normalize_route(route_match.route.path)
    already_there = bool(target_path and target_path == here)
    lookup = is_feature_lookup_query(message, classification=classification)
    strong = (
        lookup
        or classification.is_direct_navigation
        or route_match.confidence >= 0.5
    )

    if not strong:
        return FeatureFirstDecision(
            route_match=route_match,
            force_navigation_response=False,
            on_page_contextual=False,
            lock_before_llm=False,
        )

    if already_there:
        return FeatureFirstDecision(
            route_match=route_match,
            force_navigation_response=True,
            on_page_contextual=True,
            lock_before_llm=True,
        )

    return FeatureFirstDecision(
        route_match=route_match,
        force_navigation_response=True,
        on_page_contextual=False,
        lock_before_llm=True,
    )


def on_page_reply_for_route(route_id: str, label: str) -> str:
    return ON_PAGE_CONTEXT.get(
        route_id,
        f"You're already on **{label}**. The information you need is shown on this page.",
    )
