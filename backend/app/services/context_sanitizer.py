"""Filter mock LMS state so AI prompts match visible, active UI data only."""

from __future__ import annotations

import re
from typing import Any

from app.services.mock_data_loader import upcoming_exams
from app.services.route_context import normalize_route

_EXAM_QUERY_RE = re.compile(
    r"\b(exams?|tests?|assessments?|quizzes?)\b|"
    r"\bwhen\b.*\b(exam|test|assessment|quiz)\b|"
    r"\b(exam|test)\b.*\b(when|date|schedule)\b",
    re.I,
)
_COURSE_QUERY_RE = re.compile(
    r"\b(courses?|enrolled|enrollments?|modules?|lessons?)\b",
    re.I,
)
_CERT_QUERY_RE = re.compile(r"\b(certificates?|certifications?)\b", re.I)
_PURCHASE_QUERY_RE = re.compile(r"\b(purchases?|orders?|bought|billing)\b", re.I)

_ACTIVE_EXAM_STATUSES = frozenset({"scheduled", "in review"})


def certified_course_ids(certificates: list[Any] | None) -> set[str]:
    ids: set[str] = set()
    for cert in certificates or []:
        if isinstance(cert, dict) and cert.get("course_id"):
            ids.add(str(cert["course_id"]))
    return ids


def is_course_active(course: dict[str, Any], certified_ids: set[str]) -> bool:
    if course.get("completed") is True:
        return False
    cid = str(course.get("id") or "")
    if cid and cid in certified_ids:
        return False
    if int(course.get("progress_pct") or 0) >= 100:
        return False
    return True


def filter_active_courses(
    courses: list[Any] | None,
    certificates: list[Any] | None = None,
) -> list[dict[str, Any]]:
    cert_ids = certified_course_ids(certificates)
    return [
        c
        for c in courses or []
        if isinstance(c, dict) and is_course_active(c, cert_ids)
    ]


def filter_active_exams(exams: list[Any] | None) -> list[dict[str, Any]]:
    return [
        e
        for e in upcoming_exams({"exams": exams or []})
        if isinstance(e, dict)
    ]


def infer_query_focus(user_message: str | None, current_route: str | None = None) -> str:
    route = normalize_route(current_route)
    msg = (user_message or "").strip()

    if route == "/demo/exams":
        return "exams"
    if route in ("/demo/courses",) or route.startswith("/demo/course/"):
        return "courses"
    if route in ("/demo/certifications", "/demo/certificates"):
        return "certifications"
    if route == "/demo/purchases":
        return "purchases"

    if not msg:
        return "general"
    if _EXAM_QUERY_RE.search(msg):
        return "exams"
    if _CERT_QUERY_RE.search(msg):
        return "certifications"
    if _PURCHASE_QUERY_RE.search(msg):
        return "purchases"
    if _COURSE_QUERY_RE.search(msg):
        return "courses"
    return "general"


def enrich_sanitized_context(
    ctx: dict[str, Any],
    *,
    user_message: str | None = None,
    current_route: str | None = None,
) -> dict[str, Any]:
    """Attach query focus and filtered active-only slices for prompts."""
    out = dict(ctx)
    route = current_route or out.get("current_route") or out.get("currentRoute")
    focus = infer_query_focus(user_message, route)
    out["query_focus"] = focus

    loaded_courses = out.get("courses") or []
    au = out.get("activeUser") or out.get("active_user")
    if isinstance(au, dict) and au.get("courses"):
        loaded_courses = au.get("courses") or loaded_courses

    certs = out.get("certificates")
    if not certs and isinstance(au, dict):
        certs = au.get("certificates")
    if not certs:
        certs = []

    exams_raw = (
        out.get("active_exams")
        or out.get("upcoming_exams")
        or out.get("upcomingExams")
        or (au.get("upcomingExams") if isinstance(au, dict) else None)
        or []
    )

    active_courses = filter_active_courses(loaded_courses, certs)
    active_exams = filter_active_exams(exams_raw if isinstance(exams_raw, list) else [])

    out["active_courses"] = active_courses
    out["active_exams"] = active_exams
    out["completed_courses_count"] = max(0, len(loaded_courses) - len(active_courses))

    if isinstance(au, dict):
        patched = dict(au)
        patched["courses"] = active_courses
        patched["upcomingExams"] = active_exams
        out["activeUser"] = patched
        out["active_user"] = patched

    return out
