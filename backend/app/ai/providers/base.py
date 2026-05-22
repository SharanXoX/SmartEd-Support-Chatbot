"""Chat completion provider protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ChatCompletionProvider(Protocol):
    name: str

    def complete_json(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Return a parsed JSON object from the model."""
