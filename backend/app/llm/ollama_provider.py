"""Ollama provider (local or cloud) via /api/chat streaming."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ..rag.prompt import SYSTEM_PROMPT, format_context
from ..rag.retriever import RetrievedChunk
from .base import LLMProvider, Message


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.model = model
        self._base_url = base_url.rstrip("/")

    async def chat_stream(
        self, messages: list[Message], chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        system = (
            SYSTEM_PROMPT
            + "\n\n说明书摘录 / Manual excerpts:\n"
            + format_context(chunks)
        )
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{self._base_url}/api/chat", json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    content = obj.get("message", {}).get("content")
                    if content:
                        yield content
                    if obj.get("done"):
                        break
