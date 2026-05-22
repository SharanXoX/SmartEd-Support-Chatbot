"""Resolved paths for adaptive support assets and legacy fallbacks."""

from pathlib import Path

# backend/app/paths.py -> parent package directory is backend/
BACKEND_ROOT: Path = Path(__file__).resolve().parents[1]
REPO_ROOT: Path = BACKEND_ROOT.parent
DEFAULT_MOCK_DATA_DIR: Path = REPO_ROOT / "mock-data"
DEFAULT_SUPPORT_ASSETS_DIR: Path = BACKEND_ROOT / "support-assets"
DEFAULT_LEGACY_FLOWS_DIR: Path = BACKEND_ROOT / "flows"
DEFAULT_DEMO_ASSETS_DIR: Path = BACKEND_ROOT / "demo-assets"
