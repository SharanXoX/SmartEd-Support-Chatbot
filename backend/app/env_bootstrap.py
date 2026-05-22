"""Load .env from repo root and backend before Settings is constructed."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("smarted.env")

# backend/app/env_bootstrap.py -> backend -> repo root
_BACKEND_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_DIR.parent


def bootstrap_env() -> list[str]:
    """Load env files in order (later files do not override already-set vars)."""
    loaded: list[str] = []
    candidates = [
        _REPO_ROOT / ".env",
        _BACKEND_DIR / ".env",
        Path.cwd() / ".env",
    ]
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        load_dotenv(resolved, override=False)
        loaded.append(str(resolved))
    return loaded


def env_status() -> dict[str, str | bool]:
    groq = bool((os.getenv("GROQ_API_KEY") or "").strip())
    openai = bool((os.getenv("OPENAI_API_KEY") or "").strip())
    return {
        "ai_provider": (os.getenv("AI_PROVIDER") or "groq").strip().lower(),
        "groq_api_key_set": groq,
        "openai_api_key_set": openai,
        "groq_model": (os.getenv("GROQ_MODEL") or "").strip() or "llama3-70b-8192",
        "cwd": os.getcwd(),
        "repo_root": str(_REPO_ROOT),
        "backend_dir": str(_BACKEND_DIR),
    }
