"""Load mock LMS state from repo mock-data/ directory (multi-user simulation)."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.paths import DEFAULT_MOCK_DATA_DIR
from app.services.lms_feature_registry import AVAILABLE_LMS_FEATURES, AVAILABLE_LMS_ROUTES

logger = logging.getLogger("smarted.mock_data")

DEFAULT_USER_ID = "alex-001"

_LEGACY_ID_MAP = {
    "demo-001": "alex-001",
    "demo-002": "jordan-001",
    "demo-003": "sam-001",
    "demo-004": "riley-001",
}


def mock_data_root() -> Path:
    return DEFAULT_MOCK_DATA_DIR.resolve()


def _users_dir() -> Path:
    return mock_data_root() / "users"


def _students_dir() -> Path:
    return mock_data_root() / "students"


@lru_cache(maxsize=1)
def _load_index() -> dict[str, Any]:
    for sub in ("users", "students"):
        path = mock_data_root() / sub / "index.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            if sub == "users":
                return {
                    "default_student_id": data.get("default_user_id") or DEFAULT_USER_ID,
                    "students": data.get("users") or [],
                }
            return data
    return {"default_student_id": DEFAULT_USER_ID, "students": []}


@lru_cache(maxsize=32)
def _load_user_file(filename: str) -> dict[str, Any] | None:
    for base in (_users_dir(), _students_dir()):
        path = base / filename
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("[MOCK] Failed to load %s: %s", path, exc)
    return None


def _normalize_user_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Map users/*.json schema to API student state."""
    sid = str(raw.get("student_id") or raw.get("id") or "")
    courses = raw.get("courses") or []
    exams = raw.get("exams") or raw.get("upcomingExams") or []
    purchases = raw.get("purchases") or []
    activity = raw.get("recent_activity") or raw.get("recentActivity") or []

    progress = raw.get("progress") or {}
    if not progress and courses:
        progress = {
            str(c.get("id")): int(c.get("progress_pct") or 0)
            for c in courses
            if isinstance(c, dict) and c.get("id")
        }

    data: dict[str, Any] = {
        "student_id": sid,
        "name": raw.get("name") or "Student",
        "email": raw.get("email") or "",
        "role": raw.get("role") or "learner",
        "profile_type": raw.get("profile_type"),
        "courses": courses,
        "exams": exams,
        "purchases": purchases,
        "certificates": raw.get("certificates") or [],
        "announcements": raw.get("announcements") or [],
        "recent_activity": activity,
        "progress": progress,
        "available_features": raw.get("available_features")
        or raw.get("availableFeatures")
        or list(AVAILABLE_LMS_FEATURES),
        "available_routes": raw.get("available_routes")
        or raw.get("availableRoutes")
        or dict(AVAILABLE_LMS_ROUTES),
    }

    announcements_path = mock_data_root() / "announcements" / "default.json"
    if announcements_path.is_file() and not data.get("announcements"):
        try:
            shared = json.loads(announcements_path.read_text(encoding="utf-8"))
            if isinstance(shared, list):
                data["announcements"] = shared
        except Exception:
            pass

    completed_ids = {
        str(c.get("id"))
        for c in courses
        if isinstance(c, dict) and int(c.get("progress_pct") or 0) >= 100
    }
    certs = data.get("certificates") or []
    if isinstance(certs, list):
        data["certificates"] = [
            c for c in certs if isinstance(c, dict) and str(c.get("course_id")) in completed_ids
        ]
    else:
        data["certificates"] = []

    return data


def list_student_profiles() -> list[dict[str, str]]:
    index = _load_index()
    out: list[dict[str, str]] = []
    for row in index.get("students") or []:
        if isinstance(row, dict) and row.get("id"):
            out.append(
                {
                    "id": str(row["id"]),
                    "name": str(row.get("name") or ""),
                    "profile_type": str(row.get("profile_type") or ""),
                }
            )
    return out


def resolve_student_id(student_id: str | None) -> str:
    if student_id and str(student_id).strip():
        sid = str(student_id).strip()
        return _LEGACY_ID_MAP.get(sid, sid)
    index = _load_index()
    return str(index.get("default_student_id") or DEFAULT_USER_ID)


def load_student_state(student_id: str | None = None) -> dict[str, Any] | None:
    sid = resolve_student_id(student_id)
    index = _load_index()
    filename: str | None = None
    for row in index.get("students") or []:
        if isinstance(row, dict) and str(row.get("id")) == sid:
            filename = str(row.get("file") or "")
            break
    if not filename:
        filename = "alex.json"
    raw = _load_user_file(filename)
    if not raw:
        return None
    return _normalize_user_record(raw)


def upcoming_exams(state: dict[str, Any]) -> list[dict[str, Any]]:
    exams = state.get("exams") or state.get("upcomingExams") or []
    return [
        e
        for e in exams
        if isinstance(e, dict) and str(e.get("status", "")).lower() in ("scheduled", "in review")
    ]
