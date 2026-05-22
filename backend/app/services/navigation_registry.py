"""Central LMS route registry for navigation-first support."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.route_context import normalize_route

# Primary page each support flow relates to (for hybrid navigate-then-guide).
FLOW_PRIMARY_ROUTES: dict[str, str] = {
    "enroll_course": "/demo/courses",
    "submit_assignment": "/demo/assignments",
    "watch_lecture": "/demo/courses",
    "view_grades": "/demo/profile",
    "download_notes": "/demo/courses",
    "password_reset": "/demo/settings",
    "payment_failed": "/demo/purchases",
    "upload_documents": "/demo/assignments",
    "profile_update": "/demo/profile",
    "account_settings": "/demo/settings",
}


@dataclass(frozen=True)
class LmsRoute:
    route_id: str
    label: str
    path: str
    keywords: tuple[str, ...]


LMS_ROUTES: tuple[LmsRoute, ...] = (
    LmsRoute("dashboard", "Dashboard", "/demo/dashboard", ("dashboard", "home", "overview", "continue learning")),
    LmsRoute(
        "announcements",
        "Announcements",
        "/demo/announcements",
        ("announcements", "announcement", "news", "updates"),
    ),
    LmsRoute(
        "courses",
        "My Courses",
        "/demo/courses",
        (
            "my courses",
            "courses",
            "enrolled",
            "course list",
            "catalog",
            "get a course",
            "find a course",
            "browse courses",
            "check my courses",
            "what courses",
            "courses have i",
            "enrolled courses",
            "my enrollments",
        ),
    ),
    LmsRoute("calendar", "Calendar", "/demo/calendar", ("calendar", "schedule", "timetable", "events")),
    LmsRoute(
        "exams",
        "Exams",
        "/demo/exams",
        (
            "exams",
            "exam",
            "upcoming exams",
            "exam dates",
            "my exams",
            "test schedule",
            "assessments",
            "midterm",
            "final quiz",
        ),
    ),
    LmsRoute(
        "certifications",
        "Certifications",
        "/demo/certifications",
        (
            "certifications",
            "certificates",
            "certificate",
            "my certifications",
            "completed certificates",
            "show certificates",
        ),
    ),
    LmsRoute(
        "purchases",
        "My Purchases",
        "/demo/purchases",
        (
            "purchases",
            "my purchases",
            "bought courses",
            "courses did i buy",
            "what did i buy",
            "what purchases",
            "purchase history",
            "order history",
            "billing history",
            "payment history",
            "orders",
            "my orders",
            "billing",
            "payments",
        ),
    ),
    LmsRoute(
        "profile",
        "Profile",
        "/demo/profile",
        (
            "profile",
            "my profile",
            "check my profile",
            "view my profile",
            "see my profile",
            "edit profile",
            "change profile",
            "update email",
            "update account",
            "account details",
        ),
    ),
    LmsRoute(
        "settings",
        "Settings",
        "/demo/settings",
        ("settings", "preferences", "password", "notifications", "open settings"),
    ),
    LmsRoute("help", "Help", "/demo/help", ("help", "support center", "customer care", "faq", "contact")),
    LmsRoute(
        "assignments",
        "Assignments",
        "/demo/assignments",
        ("assignments", "homework", "due work", "assignment list", "submit assignment"),
    ),
    LmsRoute(
        "assignment_upload",
        "Upload Assignment",
        "/demo/assignment-upload",
        ("upload assignment", "submit file", "hand in"),
    ),
    LmsRoute("quizzes", "Quizzes", "/demo/quizzes", ("quizzes", "quiz")),
    LmsRoute("notes", "Notes", "/demo/courses", ("notes", "materials", "handouts", "pdfs", "download notes")),
    LmsRoute("progress", "Progress", "/demo/profile", ("progress", "grades", "gradebook", "scores")),
)


def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[^\w]+", text.lower()) if len(t) > 1}


@dataclass(frozen=True)
class RouteMatch:
    route: LmsRoute
    confidence: float
    matched_keyword: str


def match_navigation_route(message: str) -> RouteMatch | None:
    """Score message against LMS route keywords (no hardcoded replies)."""
    msg = message.lower().strip()
    if not msg:
        return None

    best: RouteMatch | None = None
    msg_tokens = _tokenize(msg)

    for route in LMS_ROUTES:
        for kw in route.keywords:
            kw_l = kw.lower()
            if kw_l in msg:
                score = 0.55 + min(0.35, len(kw_l) / max(len(msg), 1))
                if best is None or score > best.confidence:
                    best = RouteMatch(route=route, confidence=min(score, 0.98), matched_keyword=kw)
                continue
            kw_tokens = _tokenize(kw_l)
            if kw_tokens and kw_tokens.issubset(msg_tokens):
                score = 0.48 + 0.1 * len(kw_tokens)
                if best is None or score > best.confidence:
                    best = RouteMatch(route=route, confidence=min(score, 0.92), matched_keyword=kw)

    return best


def route_for_flow(flow_intent: str) -> LmsRoute | None:
    path = FLOW_PRIMARY_ROUTES.get(flow_intent)
    if not path:
        return None
    norm = normalize_route(path)
    for route in LMS_ROUTES:
        if normalize_route(route.path) == norm:
            return route
    return None


def registry_as_prompt_block() -> str:
    lines = ["LMS_ROUTE_REGISTRY (use for navigation_actions.path):"]
    for r in LMS_ROUTES:
        lines.append(f"- {r.label}: {r.path} (keywords: {', '.join(r.keywords[:5])}…)")
    return "\n".join(lines)
