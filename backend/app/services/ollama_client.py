from __future__ import annotations

from typing import Any

import httpx


async def chat(
    *,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    timeout: float = 60.0,
    response_format: str | None = None,
) -> str | None:
    """Call Ollama's native /api/chat endpoint and return assistant text."""
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    if response_format:
        payload["format"] = response_format

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

    message = data.get("message") or {}
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str) and content.strip():
        return content.strip()
    return None
