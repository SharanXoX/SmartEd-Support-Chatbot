"""Query context resolver tests."""

from app.services.query_context_resolver import (
    QueryCategory,
    QueryOutcome,
    extract_target_course,
    resolve_query_context,
    should_apply_deterministic_response,
)


def _priya_ctx():
    return {
        "student_id": "priya-001",
        "courses": [
            {"id": "PY101", "title": "Python Fundamentals", "progress_pct": 100, "completed": True},
            {"id": "BIO101", "title": "Introduction to Biology", "progress_pct": 100, "completed": True},
            {"id": "DS201", "title": "Data Science Essentials", "progress_pct": 88},
            {"id": "UX101", "title": "UI/UX Basics", "progress_pct": 76},
        ],
        "certificates": [
            {"course_id": "PY101", "course_title": "Python Fundamentals", "issued_at": "Apr 15, 2026"},
            {"course_id": "BIO101", "course_title": "Introduction to Biology", "issued_at": "Apr 28, 2026"},
        ],
        "exams": [
            {
                "id": "ex-ds",
                "title": "Data Science Final",
                "course_id": "DS201",
                "course": "Data Science Essentials",
                "date": "June 18, 2026 · 9:00 AM",
                "status": "Scheduled",
            },
            {
                "id": "ex-ux",
                "title": "UI/UX Final Quiz",
                "course_id": "UX101",
                "course": "UI/UX Basics",
                "date": "June 10, 2026 · 11:30 AM",
                "status": "Scheduled",
            },
        ],
    }


def _alex_ctx():
    return {
        "student_id": "alex-001",
        "courses": [
            {"id": "BIO101", "title": "Introduction to Biology", "progress_pct": 42},
            {"id": "PY101", "title": "Python Fundamentals", "progress_pct": 58},
        ],
        "certificates": [],
        "exams": [
            {
                "id": "ex-bio",
                "title": "Biology Midterm",
                "course_id": "BIO101",
                "course": "Introduction to Biology",
                "date": "May 28, 2026 · 10:00 AM",
                "status": "Scheduled",
            },
        ],
    }


def test_priya_biology_exam_completed():
    res = resolve_query_context("When is my biology exam?", _priya_ctx())
    assert res.category == QueryCategory.EXAM
    assert res.entity is not None
    assert res.outcome == QueryOutcome.COMPLETED_CERTIFIED
    assert "completed" in (res.deterministic_reply or "").lower()
    assert "Python" not in (res.deterministic_reply or "")
    assert should_apply_deterministic_response(res)


def test_alex_biology_exam_scheduled():
    res = resolve_query_context("When is my biology exam?", _alex_ctx())
    assert res.outcome == QueryOutcome.ACTIVE_EXAM
    assert "Biology Midterm" in (res.deterministic_reply or "")
    assert "May 28" in (res.deterministic_reply or "")


def test_priya_general_exams_unscoped():
    res = resolve_query_context("When do I have my exams?", _priya_ctx())
    assert res.category == QueryCategory.EXAM
    assert res.outcome == QueryOutcome.UNSCOPED
    assert not should_apply_deterministic_response(res)
    assert res.minimal_prompt
    assert "Data Science Final" in res.minimal_prompt
    assert "Python" not in res.minimal_prompt


def test_extract_biology_entity():
    courses = [{"id": "BIO101", "title": "Introduction to Biology", "progress_pct": 42}]
    ent = extract_target_course("biology exam", courses)
    assert ent is not None
    assert ent.course_id == "BIO101"
