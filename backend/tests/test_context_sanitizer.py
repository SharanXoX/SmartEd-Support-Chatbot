"""Context sanitizer unit tests."""

from app.services.context_sanitizer import (
    filter_active_courses,
    filter_active_exams,
    infer_query_focus,
    is_course_active,
)


def test_priya_excludes_completed_python():
    courses = [
        {"id": "PY101", "title": "Python Fundamentals", "progress_pct": 100, "completed": True},
        {"id": "DS201", "title": "Data Science Essentials", "progress_pct": 88},
    ]
    certs = [{"course_id": "PY101", "course_title": "Python Fundamentals"}]
    active = filter_active_courses(courses, certs)
    assert len(active) == 1
    assert active[0]["id"] == "DS201"
    assert not is_course_active(courses[0], {"PY101"})


def test_priya_exams_only_scheduled():
    exams = [
        {"title": "Data Science Final", "date": "June 18", "status": "Scheduled"},
        {"title": "Old Quiz", "date": "Jan 1", "status": "Completed"},
    ]
    active = filter_active_exams(exams)
    assert len(active) == 1
    assert active[0]["title"] == "Data Science Final"


def test_infer_exam_question_focus():
    assert infer_query_focus("When do I have my exams?", None) == "exams"
