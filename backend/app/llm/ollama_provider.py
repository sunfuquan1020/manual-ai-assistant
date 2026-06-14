"""Ollama provider (local or cloud) via /api/chat streaming."""
from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator

import httpx

from ..rag.prompt import SYSTEM_PROMPT, format_context
from ..rag.retriever import RetrievedChunk
from .base import DeviceIdentification, LLMProvider, Message
from .vision import VISION_INSTRUCTION, parse_identification


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, http_client: httpx.AsyncClient | None = None) -> None:
        self.model = model
        self._base_url = base_url.rstrip("/")
        # http_client is injectable for recorded/replay tests (httpx MockTransport).
        self._http_client = http_client

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
        client = self._http_client or httpx.AsyncClient(timeout=None)
        owns = self._http_client is None
        try:
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
        finally:
            if owns:
                await client.aclose()

    async def identify_device(
        self, image_bytes: bytes, media_type: str
    ) -> DeviceIdentification:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": VISION_INSTRUCTION, "images": [b64]}],
            "stream": False,
            "format": "json",
        }
        client = self._http_client or httpx.AsyncClient(timeout=120.0)
        owns = self._http_client is None
        try:
            resp = await client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        finally:
            if owns:
                await client.aclose()
        return parse_identification(data.get("message", {}).get("content", ""))
