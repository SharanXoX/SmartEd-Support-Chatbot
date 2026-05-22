"""Demo LMS route labels for route-aware AI support."""

from __future__ import annotations

ROUTE_LABELS: dict[str, str] = {
    "/demo/dashboard": "Dashboard (home, continue learning, overview)",
    "/demo/announcements": "Announcements",
    "/demo/courses": "My Courses (enrolled courses list)",
    "/demo/calendar": "Calendar (learning schedule)",
    "/demo/exams": "Exams (upcoming tests and assessments)",
    "/demo/certifications": "Certifications (certificates after 100% course completion)",
    "/demo/purchases": "My Purchases (order history)",
    "/demo/profile": "Profile (account details, edit profile)",
    "/demo/settings": "Settings (password, notifications, preferences)",
    "/demo/help": "Help & support",
    "/demo/assignments": "Assignments (due work and instructions)",
    "/demo/assignment-upload": "Assignment Upload (attach and submit files)",
    "/demo/quizzes": "Quizzes (legacy)",
    "/demo/certificates": "Certifications (redirect)",
}

COURSE_ROUTE_PREFIX = "/demo/course/"


def normalize_route(path: str | None) -> str:
    if not path or not str(path).strip():
        return ""
    p = str(path).strip()
    if p.startswith("#"):
        p = p[1:]
    if not p.startswith("/"):
        p = f"/{p}"
    return p.split("?")[0].rstrip("/") or "/"


def describe_route(path: str | None) -> str:
    route = normalize_route(path)
    if not route:
        return "unknown"
    if route in ROUTE_LABELS:
        return ROUTE_LABELS[route]
    if route.startswith(COURSE_ROUTE_PREFIX):
        course_id = route[len(COURSE_ROUTE_PREFIX) :]
        return f"Course detail page (course id: {course_id})"
    if route.startswith("/demo/policy/"):
        return f"Policy page ({route})"
    return route


def build_route_context_prompt(current_route: str | None) -> str:
    route = normalize_route(current_route)
    if not route:
        return ""
    label = describe_route(route)
    lines = [
        "LMS_CURRENT_PAGE:",
        f"- path: {route}",
        f"- section: {label}",
        "Route-aware rules:",
        "- Do NOT tell the user to navigate to the page they are already on unless a sub-action is needed.",
        "- Give next-step guidance for THIS page (e.g. which button to click, which course row to open).",
        "- When suggesting navigation elsewhere, include navigation_actions with label and path (demo paths like /demo/courses).",
        "- Simple 'open/go to' requests should use navigation_actions only — no screenshot walkthrough.",
    ]
    if route == "/demo/courses":
        lines.append(
            "- User is already on My Courses: suggest opening a specific course (Continue) rather than 'go to courses'."
        )
    elif route == "/demo/assignments":
        lines.append("- User is on Assignments: guide them to pick an assignment or open upload.")
    elif route == "/demo/exams":
        lines.append(
            "- User is on Exams: reference ONLY scheduled exams listed on this page — "
            "never completed/certified courses or historical enrollments."
        )
    elif route == "/demo/certifications":
        lines.append(
            "- User is on Certifications: certificates appear only after a course reaches 100% completion. "
            "If none are shown, explain that requirement briefly."
        )
    elif route == "/demo/profile":
        lines.append("- User is on Profile: help them edit fields here; do not send them to Settings unless they ask.")
    return "\n".join(lines)
