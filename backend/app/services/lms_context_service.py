"""Build LMS context snapshots for AI prompts from client state + mock data."""

from __future__ import annotations

import json
from typing import Any

from app.services.lms_feature_registry import (
    AVAILABLE_LMS_FEATURES,
    AVAILABLE_LMS_ROUTES,
    registry_prompt_block,
)
from app.services.context_sanitizer import (
    enrich_sanitized_context,
    filter_active_courses,
    filter_active_exams,
    infer_query_focus,
)
from app.services.mock_data_loader import load_student_state, upcoming_exams
from app.services.route_context import describe_route, normalize_route


def _active_user_block(lms_context: dict[str, Any], loaded: dict[str, Any] | None) -> dict[str, Any]:
    au = lms_context.get("activeUser") or lms_context.get("active_user")
    if isinstance(au, dict) and au.get("id"):
        return au
    student = lms_context.get("student") or {}
    sid = str(
        student.get("student_id")
        or lms_context.get("student_id")
        or (loaded or {}).get("student_id")
        or ""
    )
    source = loaded or {}
    courses = lms_context.get("courses") or source.get("courses") or []
    return {
        "id": sid,
        "name": student.get("name") or source.get("name") or "Student",
        "email": student.get("email") or source.get("email") or "",
        "role": student.get("role") or source.get("role") or "learner",
        "profile_type": source.get("profile_type"),
        "purchases": lms_context.get("purchases") or source.get("purchases") or [],
        "courses": courses,
        "certificates": source.get("certificates") or [],
        "upcomingExams": lms_context.get("upcoming_exams")
        or lms_context.get("upcomingExams")
        or upcoming_exams(source),
        "progress": source.get("progress") or {},
    }


def build_lms_context_prompt(
    lms_context: dict[str, Any] | None,
    *,
    user_message: str | None = None,
) -> str:
    if not lms_context:
        return registry_prompt_block()

    ctx = enrich_sanitized_context(
        lms_context,
        user_message=user_message,
        current_route=lms_context.get("current_route") or lms_context.get("currentRoute"),
    )

    route = normalize_route(ctx.get("current_route") or ctx.get("currentRoute"))
    page = ctx.get("current_page") or ctx.get("currentPage") or describe_route(route)
    sid = ctx.get("student_id") or (ctx.get("student") or {}).get("student_id")
    loaded = load_student_state(str(sid) if sid else None)
    active = _active_user_block(ctx, loaded)

    focus = ctx.get("query_focus") or infer_query_focus(user_message, route)
    all_courses = active.get("courses") or []
    certs = active.get("certificates") or []
    active_courses = ctx.get("active_courses") or filter_active_courses(all_courses, certs)
    active_exams = ctx.get("active_exams") or filter_active_exams(
        active.get("upcomingExams") or ctx.get("upcoming_exams") or []
    )
    purchases = active.get("purchases") or []
    activity = ctx.get("recent_activity") or ctx.get("recentActivity") or []
    features = ctx.get("available_features") or ctx.get("availableFeatures") or list(
        AVAILABLE_LMS_FEATURES
    )
    routes = ctx.get("available_routes") or ctx.get("availableRoutes") or AVAILABLE_LMS_ROUTES
    completed_n = int(ctx.get("completed_courses_count") or max(0, len(all_courses) - len(active_courses)))

    lines = [
        "LMS_ACTIVE_USER_CONTEXT (ONLY use data for THIS student — never leak other users):",
        f"- active_user_id: {active.get('id')}",
        f"- name: {active.get('name')}",
        f"- email: {active.get('email')}",
        f"- profile_type: {active.get('profile_type') or 'learner'}",
        f"- current_route: {route or 'unknown'}",
        f"- current_page: {page}",
        f"- query_focus: {focus}",
        f"- active_incomplete_courses_count: {len(active_courses)}",
        f"- completed_or_certified_courses_count: {completed_n} (do NOT use for exams or scheduling)",
        f"- purchases_count: {len(purchases)}",
        f"- certificates_count: {len(certs)}",
    ]

    if focus == "exams":
        lines.append(
            "EXAM CONTEXT RULE: For exam dates/schedules, use ONLY upcoming_exams below. "
            "Never mention completed or certified courses (e.g. 100% progress or earned certificates)."
        )
        if active_exams:
            lines.append("- upcoming_exams (authoritative — must match Exams page):")
            for e in active_exams[:8]:
                course = e.get("course") or e.get("course_title") or ""
                extra = f" ({course})" if course else ""
                lines.append(f"  • {e.get('title')}{extra} — {e.get('date')} [{e.get('status')}]")
        else:
            lines.append("- upcoming_exams: (none scheduled)")
    else:
        if active_courses:
            lines.append("- active_incomplete_courses:")
            for c in active_courses[:8]:
                lines.append(
                    f"  • {c.get('title')} ({c.get('progress_pct')}% complete)"
                )
        elif not all_courses:
            lines.append("- active_incomplete_courses: (none — not enrolled yet)")
        else:
            lines.append("- active_incomplete_courses: (none — all enrollments completed)")
        if focus != "purchases" and active_exams:
            lines.append("- upcoming_exams:")
            for e in active_exams[:6]:
                lines.append(f"  • {e.get('title')} — {e.get('date')}")
        if focus == "purchases" and purchases:
            lines.append("- purchases:")
            for p in purchases[:6]:
                if isinstance(p, dict):
                    lines.append(f"  • {p.get('courseTitle') or p.get('course_id')}")

    if focus == "purchases" and purchases:
        pass  # listed above
    elif focus not in ("exams", "courses") and purchases:
        lines.append(f"- purchases_count_note: {len(purchases)} total (omit unless user asks about purchases)")

    if activity and focus == "general":
        lines.append("- recent_activity:")
        for a in activity[:4]:
            if isinstance(a, dict):
                lines.append(f"  • {a.get('text')}")

    lines.append(f"- available_features: {', '.join(str(f) for f in features)}")
    if isinstance(routes, dict):
        lines.append(f"- available_routes: {json.dumps(routes, separators=(',', ':'))}")
    lines.append(
        "SESSION RULES: Answer ONLY from this active user's data. Responses must match visible LMS pages."
    )
    lines.append(
        "ANTI-STALE RULE: Do not reference completed/certified courses for exams, due dates, or 'what's next' unless the user asks about history."
    )
    lines.append(registry_prompt_block())
    return "\n".join(lines)


def merge_client_lms_context(
    lms_context: dict[str, Any] | None,
    *,
    student_id: str | None = None,
    user_message: str | None = None,
    current_route: str | None = None,
) -> dict[str, Any]:
    """Enrich partial client payload with server mock state when needed."""
    base = dict(lms_context or {})
    sid = (
        base.get("student_id")
        or (base.get("activeUser") or {}).get("id")
        or (base.get("student") or {}).get("student_id")
        or student_id
    )
    loaded = load_student_state(str(sid) if sid else None)
    if loaded:
        if not base.get("student"):
            base["student"] = {
                "student_id": loaded.get("student_id"),
                "name": loaded.get("name"),
                "email": loaded.get("email"),
                "role": loaded.get("role"),
            }
        base["student_id"] = loaded.get("student_id")
        if not base.get("courses"):
            base["courses"] = loaded.get("courses")
        if not base.get("purchases"):
            base["purchases"] = loaded.get("purchases")
        if not base.get("upcoming_exams"):
            base["upcoming_exams"] = upcoming_exams(loaded)
        if not base.get("recent_activity"):
            base["recent_activity"] = loaded.get("recent_activity")
        base["activeUser"] = _active_user_block(base, loaded)
        base["has_enrolled_courses"] = len(loaded.get("courses") or []) > 0
        base["has_purchases"] = len(loaded.get("purchases") or []) > 0
        base["certificates_count"] = len(loaded.get("certificates") or [])
    if not base.get("available_features"):
        base["available_features"] = list(AVAILABLE_LMS_FEATURES)
    if not base.get("available_routes"):
        base["available_routes"] = dict(AVAILABLE_LMS_ROUTES)
    route = current_route or base.get("current_route") or base.get("currentRoute")
    enriched = enrich_sanitized_context(
        base,
        user_message=user_message,
        current_route=route,
    )
    from app.services.query_context_resolver import classify_query_category

    focus_map = {
        "exam_query": "exams",
        "course_query": "courses",
        "certification_query": "certifications",
        "purchase_query": "purchases",
        "navigation_query": "navigation",
        "workflow_query": "workflow",
        "general_query": "general",
    }
    enriched["query_focus"] = focus_map.get(
        classify_query_category(user_message or "", route).value,
        "general",
    )
    return enriched
