"""Canonical LMS features and routes — AI must not invent beyond this registry."""

from __future__ import annotations

AVAILABLE_LMS_FEATURES: tuple[str, ...] = (
    "dashboard",
    "announcements",
    "courses",
    "calendar",
    "exams",
    "certifications",
    "purchases",
    "profile",
    "settings",
    "help",
    # Legacy areas still reachable for support flows (not primary sidebar)
    "assignments",
    "assignment_upload",
    "quizzes",
    "course_detail",
    "policy",
)

AVAILABLE_LMS_ROUTES: dict[str, str] = {
    "dashboard": "/demo/dashboard",
    "announcements": "/demo/announcements",
    "courses": "/demo/courses",
    "calendar": "/demo/calendar",
    "exams": "/demo/exams",
    "certifications": "/demo/certifications",
    "purchases": "/demo/purchases",
    "profile": "/demo/profile",
    "settings": "/demo/settings",
    "help": "/demo/help",
    "assignments": "/demo/assignments",
    "assignment_upload": "/demo/assignment-upload",
    "quizzes": "/demo/quizzes",
}

FEATURE_LABELS: dict[str, str] = {
    "dashboard": "Dashboard",
    "announcements": "Announcements",
    "courses": "My Courses",
    "calendar": "Calendar",
    "exams": "Exams",
    "certifications": "Certifications",
    "purchases": "My Purchases",
    "profile": "Profile",
    "settings": "Settings",
    "help": "Help",
}


def registry_prompt_block() -> str:
    routes = ", ".join(f"{k}={v}" for k, v in AVAILABLE_LMS_ROUTES.items())
    features = ", ".join(AVAILABLE_LMS_FEATURES)
    return (
        "LMS_FEATURE_REGISTRY (ONLY navigate to paths listed here — never invent pages):\n"
        f"- available_features: {features}\n"
        f"- available_routes: {routes}\n"
        "- If the student asks for a feature NOT in this list (e.g. attendance, hostel, payroll), "
        "do NOT navigate. Explain it is unavailable in this LMS."
    )
