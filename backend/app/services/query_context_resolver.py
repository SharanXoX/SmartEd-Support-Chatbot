"""
Query-aware context resolution — deterministic orchestration before LLM.

Flow: User query → category + entity → state validation → minimal context / fixed reply.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.context_sanitizer import (
    certified_course_ids,
    filter_active_courses,
    filter_active_exams,
    is_course_active,
)
from app.services.query_classifier import classify_query
from app.services.route_context import normalize_route

# --- Query categories ---

class QueryCategory(str, Enum):
    EXAM = "exam_query"
    COURSE = "course_query"
    CERTIFICATION = "certification_query"
    PURCHASE = "purchase_query"
    NAVIGATION = "navigation_query"
    WORKFLOW = "workflow_query"
    GENERAL = "general_query"


class QueryOutcome(str, Enum):
    NOT_ENROLLED = "not_enrolled"
    COMPLETED_CERTIFIED = "completed_certified"
    ACTIVE_EXAM = "active_exam"
    NO_EXAM_SCHEDULED = "no_exam_scheduled"
    ACTIVE_COURSE = "active_course"
    HAS_CERTIFICATE = "has_certificate"
    NO_CERTIFICATE = "no_certificate"
    HAS_PURCHASE = "has_purchase"
    NO_PURCHASE = "no_purchase"
    UNSCOPED = "unscoped"  # generic list / defer to orchestrator


_EXAM_RE = re.compile(
    r"\b(exams?|tests?|assessments?|quizzes?|midterm|final)\b|"
    r"\bwhen\b.*\b(exam|test|quiz|assessment)\b|"
    r"\b(exam|test|quiz)\b.*\b(when|date|schedule|time)\b",
    re.I,
)
_COURSE_RE = re.compile(
    r"\b(courses?|enrolled|enrollment|module|lesson|progress|continue)\b",
    re.I,
)
_CERT_RE = re.compile(r"\b(certificates?|certifications?|certified|credential)\b", re.I)
_PURCHASE_RE = re.compile(
    r"\b(purchases?|orders?|bought|billing|payment|receipt)\b",
    re.I,
)
_NAV_RE = re.compile(
    r"\b(open|go\s+to|show\s+my|view\s+my|check\s+my|see\s+my|take\s+me|navigate)\b",
    re.I,
)

_STOPWORDS = frozenset(
    {
        "a", "an", "the", "my", "me", "i", "is", "are", "when", "what", "where",
        "how", "do", "does", "have", "has", "for", "in", "on", "at", "to", "of",
        "course", "courses", "exam", "exams", "test", "certificate", "certificates",
        "show", "open", "view", "check", "see", "get", "scheduled", "upcoming",
    }
)


@dataclass(frozen=True)
class EntityMatch:
    course_id: str
    title: str
    matched_term: str
    score: float


@dataclass
class QueryResolution:
    category: QueryCategory
    outcome: QueryOutcome
    user_message: str
    entity: EntityMatch | None = None
    deterministic_reply: str | None = None
    minimal_prompt: str | None = None
    suggest_nav_path: str | None = None
    scoped_exams: list[dict[str, Any]] = field(default_factory=list)
    scoped_courses: list[dict[str, Any]] = field(default_factory=list)
    scoped_purchases: list[dict[str, Any]] = field(default_factory=list)
    scoped_certificates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def entity_matched(self) -> bool:
        return self.entity is not None

    @property
    def use_deterministic_reply(self) -> bool:
        return bool(self.deterministic_reply and self.entity_matched)


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def _course_search_terms(course: dict[str, Any]) -> list[tuple[str, float]]:
    title = str(course.get("title") or "")
    cid = str(course.get("id") or "")
    norm = _normalize_text(title)
    terms: list[tuple[str, float]] = []
    if norm:
        terms.append((norm, 1.0))
    words = [w for w in norm.split() if w and w not in _STOPWORDS and len(w) > 2]
    for w in words:
        terms.append((w, 0.85))
    if cid:
        terms.append((_normalize_text(cid), 0.7))
    # common subject aliases
    alias_map = {
        "biology": ["bio", "biology"],
        "python": ["python", "py"],
        "data science": ["data", "science", "ds"],
        "ui/ux": ["uiux", "ui", "ux", "uiux"],
        "introduction": ["intro"],
    }
    for key, extras in alias_map.items():
        if key in norm:
            for ex in extras:
                terms.append((ex, 0.9))
    return terms


def extract_target_course(
    message: str,
    courses: list[dict[str, Any]],
) -> EntityMatch | None:
    msg_norm = _normalize_text(message)
    if not msg_norm:
        return None

    best: EntityMatch | None = None
    for course in courses:
        if not isinstance(course, dict):
            continue
        cid = str(course.get("id") or "")
        title = str(course.get("title") or "Course")
        for term, weight in _course_search_terms(course):
            if len(term) < 3 and term not in ("bio", "py", "ux", "ui"):
                continue
            if term in msg_norm or re.search(rf"\b{re.escape(term)}\b", msg_norm):
                score = weight * (len(term) / max(len(msg_norm), 1))
                if best is None or score > best.score:
                    best = EntityMatch(
                        course_id=cid,
                        title=title,
                        matched_term=term,
                        score=score,
                    )
    if best and best.score >= 0.08:
        return best
    return None


def classify_query_category(
    message: str,
    current_route: str | None = None,
) -> QueryCategory:
    route = normalize_route(current_route)
    msg = message.strip()
    q = classify_query(msg)

    if q.is_direct_navigation and _NAV_RE.search(msg):
        return QueryCategory.NAVIGATION
    if q.is_process_oriented and not _EXAM_RE.search(msg):
        return QueryCategory.WORKFLOW

    if route == "/demo/exams" or _EXAM_RE.search(msg):
        return QueryCategory.EXAM
    if route in ("/demo/certifications", "/demo/certificates") or _CERT_RE.search(msg):
        return QueryCategory.CERTIFICATION
    if route == "/demo/purchases" or _PURCHASE_RE.search(msg):
        return QueryCategory.PURCHASE
    if route in ("/demo/courses",) or route.startswith("/demo/course/") or _COURSE_RE.search(msg):
        return QueryCategory.COURSE
    if q.is_direct_navigation:
        return QueryCategory.NAVIGATION
    return QueryCategory.GENERAL


def _student_state(lms_context: dict[str, Any]) -> dict[str, Any]:
    courses = lms_context.get("courses") or []
    au = lms_context.get("activeUser") or lms_context.get("active_user")
    if isinstance(au, dict):
        if au.get("courses"):
            courses = au.get("courses") or courses
    loaded = lms_context
    if not courses and lms_context.get("student_id"):
        from app.services.mock_data_loader import load_student_state

        loaded = load_student_state(str(lms_context.get("student_id"))) or lms_context
        courses = loaded.get("courses") or []

    certs = lms_context.get("certificates") or loaded.get("certificates") or []
    if isinstance(au, dict) and au.get("certificates"):
        certs = au.get("certificates") or certs

    exams_raw = (
        lms_context.get("exams")
        or lms_context.get("upcoming_exams")
        or lms_context.get("active_exams")
        or loaded.get("exams")
        or []
    )
    purchases = lms_context.get("purchases") or loaded.get("purchases") or []

    return {
        "courses": [c for c in courses if isinstance(c, dict)],
        "certificates": [c for c in certs if isinstance(c, dict)],
        "exams": [e for e in exams_raw if isinstance(e, dict)],
        "purchases": [p for p in purchases if isinstance(p, dict)],
    }


def _cert_for_course(certificates: list[dict[str, Any]], course_id: str) -> dict[str, Any] | None:
    for cert in certificates:
        if str(cert.get("course_id")) == course_id:
            return cert
    return None


def _exams_for_course(exams: list[dict[str, Any]], course_id: str) -> list[dict[str, Any]]:
    return [
        e
        for e in filter_active_exams(exams)
        if str(e.get("course_id") or "") == course_id
        or course_id.lower() in _normalize_text(str(e.get("course") or ""))
    ]


def _short_subject(title: str) -> str:
    norm = _normalize_text(title)
    for word in ("introduction", "to", "the", "essentials", "basics", "fundamentals"):
        norm = norm.replace(word, " ")
    parts = [p for p in norm.split() if len(p) > 2]
    return parts[-1].title() if parts else title


def _resolve_exam_entity(
    entity: EntityMatch,
    *,
    all_courses: list[dict[str, Any]],
    certificates: list[dict[str, Any]],
    exams: list[dict[str, Any]],
) -> QueryResolution:
    cert_ids = certified_course_ids(certificates)
    course = next((c for c in all_courses if str(c.get("id")) == entity.course_id), None)
    cert = _cert_for_course(certificates, entity.course_id)
    active_exams = _exams_for_course(exams, entity.course_id)

    if course is None:
        subject = _short_subject(entity.title) if entity.title != "Course" else entity.matched_term.title()
        return QueryResolution(
            category=QueryCategory.EXAM,
            outcome=QueryOutcome.NOT_ENROLLED,
            user_message="",
            entity=entity,
            deterministic_reply=(
                f"You are not currently enrolled in a **{subject}** course."
            ),
            suggest_nav_path="/demo/courses",
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.EXAM,
                outcome=QueryOutcome.NOT_ENROLLED,
                entity=entity,
            ),
        )

    completed = not is_course_active(course, cert_ids) or cert is not None
    if completed:
        subject = _short_subject(entity.title)
        return QueryResolution(
            category=QueryCategory.EXAM,
            outcome=QueryOutcome.COMPLETED_CERTIFIED,
            user_message="",
            entity=entity,
            deterministic_reply=(
                f"You've already completed **{entity.title}**"
                + (" and earned certification for it" if cert else "")
                + f", so there are no upcoming **{subject}** exams."
            ),
            suggest_nav_path="/demo/certifications" if cert else "/demo/courses",
            scoped_certificates=[cert] if cert else [],
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.EXAM,
                outcome=QueryOutcome.COMPLETED_CERTIFIED,
                entity=entity,
                course=course,
                cert=cert,
            ),
        )

    if active_exams:
        exam = active_exams[0]
        return QueryResolution(
            category=QueryCategory.EXAM,
            outcome=QueryOutcome.ACTIVE_EXAM,
            user_message="",
            entity=entity,
            deterministic_reply=(
                f"Your **{exam.get('title')}** is scheduled for **{exam.get('date')}**."
            ),
            suggest_nav_path="/demo/exams",
            scoped_exams=active_exams,
            scoped_courses=[course],
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.EXAM,
                outcome=QueryOutcome.ACTIVE_EXAM,
                entity=entity,
                course=course,
                exams=active_exams,
            ),
        )

    return QueryResolution(
        category=QueryCategory.EXAM,
        outcome=QueryOutcome.NO_EXAM_SCHEDULED,
        user_message="",
        entity=entity,
        deterministic_reply=(
            f"You're enrolled in **{entity.title}**, but there's no upcoming exam scheduled "
            f"for it right now. Check **Exams** for your other assessments."
        ),
        suggest_nav_path="/demo/exams",
        scoped_courses=[course],
        minimal_prompt=_minimal_prompt_block(
            category=QueryCategory.EXAM,
            outcome=QueryOutcome.NO_EXAM_SCHEDULED,
            entity=entity,
            course=course,
        ),
    )


def _resolve_cert_entity(
    entity: EntityMatch,
    *,
    all_courses: list[dict[str, Any]],
    certificates: list[dict[str, Any]],
) -> QueryResolution:
    cert = _cert_for_course(certificates, entity.course_id)
    course = next((c for c in all_courses if str(c.get("id")) == entity.course_id), None)
    if cert:
        return QueryResolution(
            category=QueryCategory.CERTIFICATION,
            outcome=QueryOutcome.HAS_CERTIFICATE,
            user_message="",
            entity=entity,
            deterministic_reply=(
                f"You earned a certificate for **{cert.get('course_title') or entity.title}** "
                f"(issued {cert.get('issued_at')})."
            ),
            suggest_nav_path="/demo/certifications",
            scoped_certificates=[cert],
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.CERTIFICATION,
                outcome=QueryOutcome.HAS_CERTIFICATE,
                entity=entity,
                cert=cert,
            ),
        )
    if course is None:
        subject = _short_subject(entity.title)
        return QueryResolution(
            category=QueryCategory.CERTIFICATION,
            outcome=QueryOutcome.NOT_ENROLLED,
            user_message="",
            entity=entity,
            deterministic_reply=f"You are not enrolled in **{subject}**, so there is no certificate on file.",
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.CERTIFICATION,
                outcome=QueryOutcome.NOT_ENROLLED,
                entity=entity,
            ),
        )
    return QueryResolution(
        category=QueryCategory.CERTIFICATION,
        outcome=QueryOutcome.NO_CERTIFICATE,
        user_message="",
        entity=entity,
        deterministic_reply=(
            f"You haven't earned a certificate for **{entity.title}** yet — "
            "complete the course (100% progress) to unlock it."
        ),
        suggest_nav_path="/demo/courses",
        scoped_courses=[course],
        minimal_prompt=_minimal_prompt_block(
            category=QueryCategory.CERTIFICATION,
            outcome=QueryOutcome.NO_CERTIFICATE,
            entity=entity,
            course=course,
        ),
    )


def _resolve_course_entity(
    entity: EntityMatch,
    *,
    all_courses: list[dict[str, Any]],
    certificates: list[dict[str, Any]],
) -> QueryResolution:
    cert_ids = certified_course_ids(certificates)
    course = next((c for c in all_courses if str(c.get("id")) == entity.course_id), None)
    if course is None:
        subject = _short_subject(entity.title)
        return QueryResolution(
            category=QueryCategory.COURSE,
            outcome=QueryOutcome.NOT_ENROLLED,
            user_message="",
            entity=entity,
            deterministic_reply=f"You are not currently enrolled in **{subject}**.",
            suggest_nav_path="/demo/courses",
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.COURSE,
                outcome=QueryOutcome.NOT_ENROLLED,
                entity=entity,
            ),
        )
    if not is_course_active(course, cert_ids):
        earned = _cert_for_course(certificates, entity.course_id)
        return QueryResolution(
            category=QueryCategory.COURSE,
            outcome=QueryOutcome.COMPLETED_CERTIFIED,
            user_message="",
            entity=entity,
            deterministic_reply=(
                f"**{entity.title}** is complete"
                + (f" — certificate issued {earned.get('issued_at')}" if earned else ".")
            ),
            suggest_nav_path="/demo/certifications",
            scoped_courses=[course],
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.COURSE,
                outcome=QueryOutcome.COMPLETED_CERTIFIED,
                entity=entity,
                course=course,
            ),
        )
    return QueryResolution(
        category=QueryCategory.COURSE,
        outcome=QueryOutcome.ACTIVE_COURSE,
        user_message="",
        entity=entity,
        deterministic_reply=(
            f"**{entity.title}** — {course.get('progress_pct')}% complete. "
            f"Next: {course.get('next_module')} ({course.get('next_due')})."
        ),
        suggest_nav_path=f"/demo/course/{entity.course_id}",
        scoped_courses=[course],
        minimal_prompt=_minimal_prompt_block(
            category=QueryCategory.COURSE,
            outcome=QueryOutcome.ACTIVE_COURSE,
            entity=entity,
            course=course,
        ),
    )


def _resolve_purchase_entity(
    entity: EntityMatch,
    *,
    purchases: list[dict[str, Any]],
) -> QueryResolution:
    match = [
        p
        for p in purchases
        if str(p.get("course_id")) == entity.course_id
        or entity.matched_term in _normalize_text(str(p.get("courseTitle") or ""))
    ]
    if match:
        p = match[0]
        return QueryResolution(
            category=QueryCategory.PURCHASE,
            outcome=QueryOutcome.HAS_PURCHASE,
            user_message="",
            entity=entity,
            deterministic_reply=(
                f"You purchased **{p.get('courseTitle')}** on **{p.get('purchasedAt')}** "
                f"({p.get('price')})."
            ),
            suggest_nav_path="/demo/purchases",
            scoped_purchases=match,
            minimal_prompt=_minimal_prompt_block(
                category=QueryCategory.PURCHASE,
                outcome=QueryOutcome.HAS_PURCHASE,
                entity=entity,
                purchases=match,
            ),
        )
    return QueryResolution(
        category=QueryCategory.PURCHASE,
        outcome=QueryOutcome.NO_PURCHASE,
        user_message="",
        entity=entity,
        deterministic_reply=f"No purchase record found for **{entity.title}** on your account.",
        suggest_nav_path="/demo/purchases",
        minimal_prompt=_minimal_prompt_block(
            category=QueryCategory.PURCHASE,
            outcome=QueryOutcome.NO_PURCHASE,
            entity=entity,
        ),
    )


def _minimal_prompt_block(
    *,
    category: QueryCategory,
    outcome: QueryOutcome,
    entity: EntityMatch | None = None,
    course: dict[str, Any] | None = None,
    exams: list[dict[str, Any]] | None = None,
    cert: dict[str, Any] | None = None,
    purchases: list[dict[str, Any]] | None = None,
) -> str:
    lines = [
        "QUERY_SCOPED_CONTEXT (authoritative — answer ONLY from this block):",
        f"- category: {category.value}",
        f"- outcome: {outcome.value}",
    ]
    if entity:
        lines.append(f"- target_course: {entity.title} ({entity.course_id})")
    if course:
        lines.append(
            f"- course_state: {course.get('title')} @ {course.get('progress_pct')}% "
            f"(completed={course.get('completed', False)})"
        )
    if exams:
        for e in exams:
            lines.append(f"- exam: {e.get('title')} — {e.get('date')}")
    if cert:
        lines.append(f"- certificate: {cert.get('course_title')} issued {cert.get('issued_at')}")
    if purchases:
        for p in purchases:
            lines.append(f"- purchase: {p.get('courseTitle')} — {p.get('purchasedAt')}")
    lines.append("Do NOT mention other courses, exams, or purchases not listed here.")
    return "\n".join(lines)


def _resolve_unscoped(
    category: QueryCategory,
    *,
    state: dict[str, Any],
    user_message: str,
) -> QueryResolution:
    certs = state["certificates"]
    all_courses = state["courses"]
    cert_ids = certified_course_ids(certs)
    active_courses = filter_active_courses(all_courses, certs)
    active_exams = filter_active_exams(state["exams"])

    minimal: str | None = None
    if category == QueryCategory.EXAM:
        lines = ["QUERY_SCOPED_CONTEXT:", "- category: exam_query (general — no single course target)"]
        if active_exams:
            lines.append("- upcoming_exams:")
            for e in active_exams:
                lines.append(f"  • {e.get('title')} — {e.get('date')}")
        else:
            lines.append("- upcoming_exams: none")
        lines.append("Do NOT mention completed/certified courses.")
        minimal = "\n".join(lines)
        return QueryResolution(
            category=category,
            outcome=QueryOutcome.UNSCOPED,
            user_message=user_message,
            scoped_exams=active_exams,
            minimal_prompt=minimal,
        )

    if category == QueryCategory.COURSE:
        lines = ["QUERY_SCOPED_CONTEXT:", "- category: course_query (general)"]
        for c in active_courses[:6]:
            lines.append(f"  • {c.get('title')} ({c.get('progress_pct')}%)")
        minimal = "\n".join(lines) + "\nDo NOT list completed courses unless asked."
        return QueryResolution(
            category=category,
            outcome=QueryOutcome.UNSCOPED,
            user_message=user_message,
            scoped_courses=active_courses,
            minimal_prompt=minimal,
        )

    if category == QueryCategory.CERTIFICATION:
        lines = ["QUERY_SCOPED_CONTEXT:", "- category: certification_query (general)"]
        if certs:
            for c in certs:
                lines.append(f"  • {c.get('course_title')} — {c.get('issued_at')}")
        else:
            lines.append("- certificates: none")
        minimal = "\n".join(lines)
        return QueryResolution(
            category=category,
            outcome=QueryOutcome.UNSCOPED,
            user_message=user_message,
            scoped_certificates=certs,
            minimal_prompt=minimal,
        )

    if category == QueryCategory.PURCHASE:
        purchases = state["purchases"]
        lines = ["QUERY_SCOPED_CONTEXT:", "- category: purchase_query (general)"]
        for p in purchases[:6]:
            lines.append(f"  • {p.get('courseTitle')} — {p.get('purchasedAt')}")
        minimal = "\n".join(lines)
        return QueryResolution(
            category=category,
            outcome=QueryOutcome.UNSCOPED,
            user_message=user_message,
            scoped_purchases=purchases,
            minimal_prompt=minimal,
        )

    return QueryResolution(
        category=category,
        outcome=QueryOutcome.UNSCOPED,
        user_message=user_message,
        scoped_courses=active_courses,
        scoped_exams=active_exams,
    )


def resolve_query_context(
    user_message: str,
    lms_context: dict[str, Any],
    *,
    current_route: str | None = None,
) -> QueryResolution:
    """Resolve query category, entity, outcome, and minimal context for this turn."""
    msg = user_message.strip()
    category = classify_query_category(msg, current_route)
    state = _student_state(lms_context)
    all_courses = state["courses"]

    # Load full course list from raw state for entity matching (includes completed)
    raw_courses = lms_context.get("courses") or all_courses
    au = lms_context.get("activeUser") or lms_context.get("active_user")
    if isinstance(au, dict) and not len(raw_courses):
        from app.services.mock_data_loader import load_student_state

        sid = lms_context.get("student_id") or au.get("id")
        if sid:
            loaded = load_student_state(str(sid))
            if loaded:
                raw_courses = loaded.get("courses") or raw_courses

    entity = extract_target_course(msg, raw_courses if isinstance(raw_courses, list) else all_courses)

    if category in (QueryCategory.NAVIGATION, QueryCategory.WORKFLOW):
        return QueryResolution(
            category=category,
            outcome=QueryOutcome.UNSCOPED,
            user_message=msg,
            entity=entity,
        )

    if entity and category == QueryCategory.EXAM:
        res = _resolve_exam_entity(
            entity,
            all_courses=raw_courses if isinstance(raw_courses, list) else all_courses,
            certificates=state["certificates"],
            exams=state["exams"],
        )
        res.user_message = msg
        return res

    if entity and category == QueryCategory.CERTIFICATION:
        res = _resolve_cert_entity(
            entity,
            all_courses=raw_courses if isinstance(raw_courses, list) else all_courses,
            certificates=state["certificates"],
        )
        res.user_message = msg
        return res

    if entity and category == QueryCategory.COURSE:
        res = _resolve_course_entity(
            entity,
            all_courses=raw_courses if isinstance(raw_courses, list) else all_courses,
            certificates=state["certificates"],
        )
        res.user_message = msg
        return res

    if entity and category == QueryCategory.PURCHASE:
        res = _resolve_purchase_entity(entity, purchases=state["purchases"])
        res.user_message = msg
        return res

    # Exam phrasing with embedded course but category general
    if entity and _EXAM_RE.search(msg):
        res = _resolve_exam_entity(
            entity,
            all_courses=raw_courses if isinstance(raw_courses, list) else all_courses,
            certificates=state["certificates"],
            exams=state["exams"],
        )
        res.user_message = msg
        return res

    return _resolve_unscoped(category, state=state, user_message=msg)


def should_apply_deterministic_response(
    resolution: QueryResolution,
    *,
    orchestrator_mode: str | None = None,
) -> bool:
    """Use system-authored reply for entity-specific queries (not generic navigation)."""
    if not resolution.use_deterministic_reply:
        return False
    if resolution.category == QueryCategory.NAVIGATION:
        return False
    if orchestrator_mode == "navigate_only" and resolution.outcome == QueryOutcome.UNSCOPED:
        return False
    return True


def build_deterministic_chat_response(
    resolution: QueryResolution,
    *,
    current_route: str | None = None,
) -> dict[str, Any]:
    """Payload fields for ChatTurnResponse from resolver."""
    from app.schemas import NavigationAction

    here = normalize_route(current_route)
    nav_path = normalize_route(resolution.suggest_nav_path) if resolution.suggest_nav_path else ""
    nav_actions = []
    if nav_path and nav_path != here:
        label = "Open page"
        if "exam" in nav_path:
            label = "Open Exams"
        elif "course" in nav_path:
            label = "Open course"
        elif "cert" in nav_path:
            label = "Open Certifications"
        elif "purchase" in nav_path:
            label = "Open Purchases"
        nav_actions = [NavigationAction(label=label, path=nav_path)]

    return {
        "reply": resolution.deterministic_reply or "",
        "intent": resolution.category.value,
        "confidence": 0.92,
        "response_source": "query_resolver",
        "response_type": "query_resolver",
        "response_mode": "conversational",
        "navigation_actions": nav_actions,
    }
