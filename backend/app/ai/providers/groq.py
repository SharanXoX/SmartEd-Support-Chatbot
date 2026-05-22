"""Groq Cloud LLM (OpenAI-compatible chat API)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from groq import Groq

logger = logging.getLogger("smarted.ai.groq")

USER_FACING_ERROR = (
    "I'm having trouble accessing advanced AI support right now, but I can still help "
    "with guided troubleshooting. Try a topic like password reset or payment help."
)


class GroqProvider:
    name = "groq"

    def __init__(self, *, api_key: str, model: str, max_retries: int = 2, timeout: float = 60.0) -> None:
        self._client = Groq(api_key=api_key, timeout=timeout)
        self._model = model
        self._max_retries = max_retries

    def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        last_err: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                logger.info(
                    "[AI] Groq request model=%s messages=%d attempt=%d",
                    self._model,
                    len(messages),
                    attempt + 1,
                )
                completion = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                raw = completion.choices[0].message.content or "{}"
                data = json.loads(raw)
                logger.info("[AI] Groq response received keys=%s", list(data.keys()))
                return data
            except Exception as exc:
                last_err = exc
                logger.exception("[AI] Groq error attempt=%d: %s", attempt + 1, exc)
                if attempt < self._max_retries:
                    time.sleep(0.6 * (attempt + 1))
        raise RuntimeError(USER_FACING_ERROR) from last_err
