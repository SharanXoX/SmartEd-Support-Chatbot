"""Diagnostics for env loading and AI provider wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.ai.provider_factory import get_chat_provider
from app.config import Settings, get_settings
from app.env_bootstrap import bootstrap_env, env_status
from app.services.support_indexer import get_support_indexer

router = APIRouter(prefix="/debug", tags=["debug"])


def _require_debug(settings: Settings) -> None:
    if not settings.enable_debug_routes:
        raise HTTPException(status_code=404, detail="Debug routes disabled")


@router.get("/env")
def debug_env(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    _require_debug(settings)
    bootstrap_env()
    raw = env_status()
    sel = get_chat_provider(settings)
    return {
        **raw,
        "settings_groq_key_set": bool(settings.groq_api_key.strip()),
        "settings_openai_key_set": bool(settings.openai_api_key.strip()),
        "requested_provider": sel.requested_provider,
        "effective_provider": sel.effective_provider,
        "provider_error": sel.error_detail,
        "groq_model": settings.groq_model,
        "database_url_scheme": settings.database_url.split(":", 1)[0],
    }


@router.get("/support-image/{flow_id}/{filename}")
def debug_support_image(
    flow_id: str,
    filename: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    _require_debug(settings)
    from app.services.asset_urls import image_exists_on_disk, public_url_for_file, to_absolute_url

    exists = image_exists_on_disk(settings, flow_id, filename)
    rel = public_url_for_file(flow_id, filename)
    return {
        "exists": exists,
        "relative_url": rel,
        "absolute_url": to_absolute_url(settings, rel, settings.public_base_url),
    }


@router.get("/support-catalog")
def debug_support_catalog(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    _require_debug(settings)
    get_support_indexer().refresh(settings, force=True)
    return get_support_indexer().catalog_summary(settings)


@router.get("/provider")
def debug_provider(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    _require_debug(settings)
    sel = get_chat_provider(settings)
    probe_ok = False
    probe_detail: str | None = None
    if sel.provider is not None:
        try:
            data = sel.provider.complete_json(
                messages=[
                    {"role": "system", "content": "Reply JSON only: {\"reply\":\"ok\",\"intent\":\"faq_general\",\"confidence\":0.9,\"follow_up_question\":null,\"visual_steps\":[],\"suggested_replies\":[],\"escalate\":false,\"citations\":[]}"},
                    {"role": "user", "content": "ping"},
                ],
                temperature=0,
            )
            probe_ok = bool(data.get("reply"))
            probe_detail = "connectivity_ok"
        except Exception as exc:
            probe_detail = str(exc)[:200]
    return {
        "requested_provider": sel.requested_provider,
        "effective_provider": sel.effective_provider,
        "groq_available": sel.groq_available,
        "openai_available": sel.openai_available,
        "provider_ready": sel.provider is not None,
        "error": sel.error_detail,
        "connectivity_probe": probe_ok,
        "probe_detail": probe_detail,
    }
