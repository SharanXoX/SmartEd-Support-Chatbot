"""Resolve support screenshot paths to browser-accessible URLs."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app.config import Settings
from app.paths import DEFAULT_SUPPORT_ASSETS_DIR

logger = logging.getLogger("smarted.assets")

LEGACY_DEMO_PREFIX = "/demo-assets/"
SUPPORT_PREFIX = "/support-assets/"

_LEGACY_FOLDER_MAP = {
    "password": "password_reset",
    "payments": "payment_failed",
    "uploads": "upload_documents",
    "profile": "profile_update",
    "account": "account_settings",
}


def support_assets_root(settings: Settings) -> Path:
    if settings.support_assets_dir:
        return Path(settings.support_assets_dir).expanduser().resolve()
    return DEFAULT_SUPPORT_ASSETS_DIR.resolve()


def public_url_for_file(flow_id: str, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{SUPPORT_PREFIX}{flow_id}/{safe_name}"


def remap_legacy_url(url: str, flow_id: str) -> str:
    """Convert /demo-assets/password/step1.png → /support-assets/password_reset/step1.png."""
    if not url.startswith(LEGACY_DEMO_PREFIX):
        return url
    rest = url[len(LEGACY_DEMO_PREFIX) :].lstrip("/")
    parts = rest.split("/", 1)
    if len(parts) != 2:
        return url
    old_folder, filename = parts[0], parts[1]
    new_folder = _LEGACY_FOLDER_MAP.get(old_folder, flow_id)
    return public_url_for_file(new_folder, filename)


def filesystem_path_for_url(settings: Settings, url: str) -> Path | None:
    if not url or url.startswith("http://") or url.startswith("https://"):
        return None
    path = url.split("?", 1)[0]
    if path.startswith(SUPPORT_PREFIX):
        rel = path[len(SUPPORT_PREFIX) :]
        return support_assets_root(settings) / rel
    if path.startswith(LEGACY_DEMO_PREFIX):
        remapped = remap_legacy_url(path, "")
        return filesystem_path_for_url(settings, remapped)
    return None


def image_exists_on_disk(settings: Settings, flow_id: str, filename: str) -> bool:
    p = support_assets_root(settings) / flow_id / Path(filename).name
    return p.is_file() and p.stat().st_size > 0


def resolve_step_image_url(
    settings: Settings,
    *,
    flow_id: str,
    image_ref: str | None,
    disk_filename: str | None = None,
) -> str | None:
    """
    Prefer a verified on-disk screenshot; normalize legacy /demo-assets paths.
    """
    root = support_assets_root(settings) / flow_id

    if disk_filename and image_exists_on_disk(settings, flow_id, disk_filename):
        return public_url_for_file(flow_id, disk_filename)

    if not image_ref:
        return None

    ref = image_ref.strip()
    if ref.startswith("http://") or ref.startswith("https://"):
        # Normalize old absolute URLs (e.g. localhost:8080) back to /support-assets/... paths.
        from urllib.parse import urlparse

        parsed = urlparse(ref)
        if parsed.path.startswith(SUPPORT_PREFIX):
            ref = parsed.path
        else:
            return ref

    if ref.startswith(LEGACY_DEMO_PREFIX):
        ref = remap_legacy_url(ref, flow_id)

    if not ref.startswith("/"):
        ref = public_url_for_file(flow_id, ref)

    fs_path = filesystem_path_for_url(settings, ref)
    if fs_path and fs_path.is_file() and fs_path.stat().st_size > 0:
        return ref

    # steps.json referenced a name — try basename under flow folder
    basename = Path(ref).name
    if image_exists_on_disk(settings, flow_id, basename):
        return public_url_for_file(flow_id, basename)

    logger.warning("[IMAGE] Missing file for flow=%s ref=%s", flow_id, image_ref)
    return None


def to_absolute_url(settings: Settings, path_or_url: str, base_url: str = "") -> str:
    if not path_or_url:
        return path_or_url
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    base = (settings.public_base_url or base_url or "").rstrip("/")
    if not base:
        return path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
    path = path_or_url if path_or_url.startswith("/") else f"/{path_or_url}"
    return f"{base}{path}"


def get_public_base_url(settings: Settings, request_headers: dict[str, str] | None = None) -> str:
    """
    Prefer the browser Origin (5173 dev / 8080 Docker) so screenshot URLs always match
    where the user opened the UI — not a stale PUBLIC_BASE_URL from .env.
    """
    if request_headers:
        origin = (request_headers.get("origin") or "").strip()
        if origin.startswith("http://") or origin.startswith("https://"):
            return origin.rstrip("/")
        proto = request_headers.get("x-forwarded-proto", "http")
        host = request_headers.get("x-forwarded-host") or request_headers.get("host", "")
        if host and "127.0.0.1:8000" not in host and ":8000" not in host:
            return f"{proto}://{host}".rstrip("/")
    if settings.public_base_url.strip():
        return settings.public_base_url.strip().rstrip("/")
    return ""


def enrich_visual_step_urls(
    settings: Settings,
    visual_steps: list,
    *,
    base_url: str = "",
) -> list:
    """Set image_url on VisualStep models — relative paths if no base, else browser-matched absolute URLs."""
    from app.schemas import VisualStep

    out: list[VisualStep] = []
    for vs in visual_steps:
        raw = vs.image_url if hasattr(vs, "image_url") else None
        if not raw and hasattr(vs, "image"):
            raw = vs.image
        if not raw:
            out.append(vs)
            continue
        flow_id = ""
        m = re.match(r"^/support-assets/([^/]+)/", raw)
        if m:
            flow_id = m.group(1)
        resolved = resolve_step_image_url(settings, flow_id=flow_id, image_ref=raw) if flow_id else raw
        if not resolved:
            out.append(vs.model_copy(update={"image_url": None}) if hasattr(vs, "model_copy") else vs)
            continue
        # Always use relative paths — the browser + Vite/nginx resolve the correct host (5173 or 8080).
        final_url = resolved
        out.append(
            vs.model_copy(update={"image_url": final_url})
            if hasattr(vs, "model_copy")
            else VisualStep(**{**vs.model_dump(), "image_url": final_url})
        )
    return out
