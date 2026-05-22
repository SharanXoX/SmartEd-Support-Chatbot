"""Detect requests for LMS capabilities that do not exist in the mock portal."""

from __future__ import annotations

import re
from dataclasses import dataclass

# (feature_key, display_name, pattern)
_UNAVAILABLE: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    (
        "attendance",
        "Attendance tracking",
        re.compile(
            r"\b("
            r"attendance\s+tracking|track\s+my\s+attendance|show\s+(?:my\s+)?attendance|"
            r"open\s+attendance|view\s+attendance|my\s+attendance|class\s+attendance|"
            r"attendance\s+record|attendance\s+page"
            r")\b",
            re.I,
        ),
    ),
    (
        "placements",
        "Placements",
        re.compile(r"\b(placements?|placement\s+cell|campus\s+placement)\b", re.I),
    ),
    ("hostel", "Hostel", re.compile(r"\b(hostel|dormitory|housing\s+block)\b", re.I)),
    ("transport", "Transport", re.compile(r"\b(bus\s+route|transport\s+schedule|shuttle)\b", re.I)),
    ("payroll", "Payroll", re.compile(r"\b(payroll|salary\s+slip|payslip)\b", re.I)),
    (
        "admin_panel",
        "Admin panel",
        re.compile(r"\b(admin\s+panel|admin\s+dashboard|instructor\s+admin)\b", re.I),
    ),
    (
        "analytics",
        "Advanced analytics",
        re.compile(r"\b(learning\s+analytics\s+dashboard|predictive\s+analytics)\b", re.I),
    ),
)

# Policy-style questions about attendance rules are allowed (informational).
_POLICY_EXCEPTION = re.compile(
    r"\b(what\s+is|what's|explain|policy|rule|requirement|percentage)\b.*\battendance\b",
    re.I,
)


@dataclass(frozen=True)
class UnavailableFeatureHit:
    feature_key: str
    label: str


def detect_unavailable_feature(message: str) -> UnavailableFeatureHit | None:
    msg = message.strip()
    if not msg:
        return None
    if _POLICY_EXCEPTION.search(msg):
        return None
    for key, label, pattern in _UNAVAILABLE:
        if pattern.search(msg):
            return UnavailableFeatureHit(feature_key=key, label=label)
    return None


def unavailable_feature_reply(hit: UnavailableFeatureHit) -> str:
    return (
        f"**{hit.label}** is currently not available in this LMS. "
        "You can use Dashboard, Announcements, My Courses, Calendar, Exams, Certifications, "
        "Purchases, Profile, Settings, or Help — or ask how to complete a learning task."
    )
