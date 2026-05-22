"""OpenAI chat provider (future / optional)."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


class OpenAIProvider:
    name = "openai"

    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw = completion.choices[0].message.content or "{}"
        return json.loads(raw)
