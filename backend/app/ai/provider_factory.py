"""Select chat provider with automatic fallback (Groq ↔ OpenAI)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.ai.providers.base import ChatCompletionProvider
from app.ai.providers.groq import GroqProvider
from app.ai.providers.openai import OpenAIProvider
from app.config import Settings

logger = logging.getLogger("smarted.ai")


@dataclass(frozen=True)
class ProviderSelection:
    provider: ChatCompletionProvider | None
    error_detail: str | None
    requested_provider: str
    effective_provider: str | None
    groq_available: bool
    openai_available: bool


def _has_key(value: str) -> bool:
    return bool(value and value.strip())


def get_chat_provider(settings: Settings) -> ProviderSelection:
    """
    Pick a working provider without hard-failing when the preferred key is missing.
    Order: preferred provider (if key present) → alternate provider (if key present).
    """
    requested = settings.ai_provider.strip().lower()
    groq_ok = _has_key(settings.groq_api_key)
    openai_ok = _has_key(settings.openai_api_key)

    if requested == "groq":
        chain: list[tuple[str, bool]] = [("groq", groq_ok), ("openai", openai_ok)]
    elif requested == "openai":
        chain = [("openai", openai_ok), ("groq", groq_ok)]
    else:
        return ProviderSelection(
            provider=None,
            error_detail=f"Unknown AI_PROVIDER={settings.ai_provider!r}. Use 'groq' or 'openai'.",
            requested_provider=requested,
            effective_provider=None,
            groq_available=groq_ok,
            openai_available=openai_ok,
        )

    for name, ok in chain:
        if not ok:
            continue
        if name == "groq":
            logger.info("[AI] Provider selected: groq (model=%s)", settings.groq_model)
            return ProviderSelection(
                provider=GroqProvider(api_key=settings.groq_api_key.strip(), model=settings.groq_model),
                error_detail=None,
                requested_provider=requested,
                effective_provider="groq",
                groq_available=True,
                openai_available=openai_ok,
            )
        if name == "openai":
            logger.info("[AI] Provider selected: openai (model=%s)", settings.openai_chat_model)
            return ProviderSelection(
                provider=OpenAIProvider(
                    api_key=settings.openai_api_key.strip(),
                    model=settings.openai_chat_model,
                ),
                error_detail=None,
                requested_provider=requested,
                effective_provider="openai",
                groq_available=groq_ok,
                openai_available=True,
            )

    missing = []
    if requested == "groq" and not groq_ok:
        missing.append("GROQ_API_KEY")
    if requested == "openai" and not openai_ok:
        missing.append("OPENAI_API_KEY")
    if not groq_ok and not openai_ok:
        detail = "No LLM API keys configured (set GROQ_API_KEY and/or OPENAI_API_KEY in .env)."
    else:
        detail = f"AI_PROVIDER={requested} but {', '.join(missing)} missing; no fallback key available."

    logger.warning("[AI] No provider available: %s", detail)
    return ProviderSelection(
        provider=None,
        error_detail=detail,
        requested_provider=requested,
        effective_provider=None,
        groq_available=groq_ok,
        openai_available=openai_ok,
    )
