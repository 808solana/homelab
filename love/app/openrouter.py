"""OpenRouter client.

OpenRouter exposes an OpenAI-compatible endpoint at {BASE}/chat/completions.
We stream tokens via SSE: each line is `data: {json}`, terminated by
`data: [DONE]`. Each chunk carries choices[0].delta.content.

We yield plain text deltas; main.py wraps them into our own SSE frames for the
browser. Errors are raised and handled by the caller so we can show the user a
useful message instead of a blank stream.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from . import config


async def stream_chat(model: str, messages: list[dict]) -> AsyncIterator[str]:
    """Stream text deltas from a model via OpenRouter."""
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env and restart."
        )

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional attribution headers OpenRouter uses for its rankings.
        "HTTP-Referer": config.SITE_URL,
        "X-Title": config.APP_TITLE,
    }
    payload = {"model": model, "messages": messages, "stream": True}

    url = f"{config.OPENROUTER_BASE_URL}/chat/completions"

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", "replace")
                raise RuntimeError(f"OpenRouter {resp.status_code}: {body[:500]}")

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[len("data: "):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    # Keepalive comments or partial frames — skip them.
                    continue
