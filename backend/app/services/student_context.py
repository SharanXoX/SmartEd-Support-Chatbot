"""Mock (and future LMS) student context for prompt injection."""



from __future__ import annotations



import json

import logging

from functools import lru_cache

from pathlib import Path

from typing import Any



from app.config import Settings

from app.paths import BACKEND_ROOT, DEFAULT_MOCK_DATA_DIR

from app.services.context_sanitizer import (

    enrich_sanitized_context,

    filter_active_courses,

    filter_active_exams,

    infer_query_focus,

)

from app.services.mock_data_loader import load_student_state



logger = logging.getLogger("smarted.student_context")



DEFAULT_MOCK_PATH = BACKEND_ROOT / "mock_student.json"





@lru_cache(maxsize=1)

def _load_legacy_mock(path: str) -> dict[str, Any] | None:

    p = Path(path).expanduser().resolve()

    if not p.is_file():

        return None

    try:

        return json.loads(p.read_text(encoding="utf-8"))

    except Exception as exc:

        logger.warning("[STUDENT] Failed to load mock context %s: %s", p, exc)

        return None





def get_mock_student(settings: Settings, student_id: str | None = None) -> dict[str, Any] | None:

    if not settings.mock_student_enabled:

        return None

    if DEFAULT_MOCK_DATA_DIR.is_dir():

        data = load_student_state(student_id)

        if data:

            return data

    raw_path = (settings.mock_student_path or "").strip()

    path = raw_path if raw_path else str(DEFAULT_MOCK_PATH)

    return _load_legacy_mock(path)





def build_student_context_prompt(

    settings: Settings,

    student_id: str | None = None,

    lms_context: dict | None = None,

    *,

    user_message: str | None = None,

) -> str:

    """System prompt block for LLM and flow orchestration."""

    sid = student_id

    route = None

    if lms_context and isinstance(lms_context, dict):

        au = lms_context.get("activeUser") or lms_context.get("active_user") or {}

        if isinstance(au, dict) and au.get("id"):

            sid = str(au.get("id"))

        elif lms_context.get("student_id"):

            sid = str(lms_context.get("student_id"))

        route = lms_context.get("current_route") or lms_context.get("currentRoute")



    data = get_mock_student(settings, sid)

    if not data:

        return ""



    ctx = (

        enrich_sanitized_context(lms_context, user_message=user_message, current_route=route)

        if lms_context

        else {}

    )

    focus = ctx.get("query_focus") or infer_query_focus(user_message, route)

    certs = data.get("certificates") or []

    active_courses = ctx.get("active_courses") or filter_active_courses(

        data.get("courses") or [], certs

    )

    active_exams = ctx.get("active_exams") or filter_active_exams(data.get("exams") or [])



    name = data.get("name") or "Student"

    role = data.get("role") or "learner"

    lines = [

        "LMS_STUDENT_CONTEXT (use for personalized, supportive guidance — do not invent enrollments):",

        f"- Name: {name}",

        f"- Role: {role}",

        f"- Context focus: {focus}",

    ]

    if data.get("profile_type"):

        lines.append(f"- Profile: {data.get('profile_type')}")



    if focus == "exams":

        lines.append(

            "- For this question, use ONLY the scheduled exams below (not completed/certified courses)."

        )

        if active_exams:

            lines.append("- Scheduled exams:")

            for e in active_exams:

                course = e.get("course") or e.get("course_title") or ""

                suffix = f" ({course})" if course else ""

                lines.append(f"  • {e.get('title')}{suffix} — {e.get('date')}")

        else:

            lines.append("- Scheduled exams: none")

    else:

        if active_courses:

            lines.append("- Active incomplete courses:")

            for c in active_courses:

                title = c.get("title") or c.get("id") or "Course"

                prog = c.get("progress_pct")

                due = c.get("next_due") or ""

                mod = c.get("next_module") or ""

                extra = ", ".join(

                    x for x in [f"{prog}% complete" if prog is not None else "", mod, due] if x

                )

                lines.append(f"  • {title}" + (f" ({extra})" if extra else ""))

        completed_n = max(0, len(data.get("courses") or []) - len(active_courses))

        if completed_n:

            lines.append(

                f"- Completed/certified courses: {completed_n} (historical — do not cite for exams or upcoming work)"

            )

        if focus != "exams" and active_exams:

            lines.append("- Upcoming exams:")

            for e in active_exams:

                lines.append(f"  • {e.get('title')} — {e.get('date')}")



    if certs and focus in ("certifications", "general"):

        lines.append(f"- Certificates earned: {len(certs)}")



    lines.append(

        "When suggesting navigation, reference only active enrollments and scheduled exams shown above. "

        "Use only demo paths from LMS_FEATURE_REGISTRY."

    )

    return "\n".join(lines)





def personalization_hint(

    settings: Settings,

    student_id: str | None = None,

    *,

    user_message: str | None = None,

    current_route: str | None = None,

    lms_context: dict | None = None,

) -> str:

    """Short line appended to navigation/bundled-flow intros — never stale completed courses."""

    sid = student_id

    if lms_context and isinstance(lms_context, dict):

        au = lms_context.get("activeUser") or lms_context.get("active_user") or {}

        if isinstance(au, dict) and au.get("id"):

            sid = str(au.get("id"))

        current_route = current_route or lms_context.get("current_route") or lms_context.get("currentRoute")



    data = get_mock_student(settings, sid)

    if not data:

        return ""



    ctx = enrich_sanitized_context(

        lms_context or {"student_id": sid},

        user_message=user_message,

        current_route=current_route,

    )

    focus = ctx.get("query_focus") or infer_query_focus(user_message, current_route)



    if focus == "exams":

        exams = ctx.get("active_exams") or filter_active_exams(data.get("exams") or [])

        if not exams:

            return ""

        first = exams[0]

        title = first.get("title") or "your exam"

        when = first.get("date") or "see Exams for the time"

        return f"Your next exam is **{title}** — {when}."



    active = ctx.get("active_courses") or filter_active_courses(

        data.get("courses") or [], data.get("certificates") or []

    )

    if not active:

        return ""

    first = active[0]

    title = first.get("title") or "your course"

    due = first.get("next_due")

    if due and due != "—":

        return f"You're working on **{title}** — next up: {due}."

    return f"You're working on **{title}** — open it from **My Courses** on your dashboard."

