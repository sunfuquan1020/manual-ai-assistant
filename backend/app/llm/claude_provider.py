"""Claude (Anthropic) provider — uses document blocks with native citations."""
from __future__ import annotations

import base64
from collections.abc import AsyncIterator

from ..rag.prompt import SYSTEM_PROMPT
from ..rag.retriever import RetrievedChunk
from .base import DeviceIdentification, LLMProvider, Message
from .vision import VISION_INSTRUCTION, VISION_SYSTEM, parse_identification


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str, http_client=None) -> None:
        import anthropic

        self.model = model
        # http_client is injectable for recorded/replay tests (httpx MockTransport).
        self._client = anthropic.AsyncAnthropic(api_key=api_key, http_client=http_client)

    async def chat_stream(
        self, messages: list[Message], chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        history = messages[:-1]
        last_user_text = messages[-1]["content"]

        # Retrieved chunks ride on the final user turn as citable documents.
        content: list[dict] = [
            {
                "type": "document",
                "source": {
                    "type": "text",
                    "media_type": "text/plain",
                    "data": c.text,
                },
                "title": f"来源 {i} (第 {c.page} 页)",
                "citations": {"enabled": True},
            }
            for i, c in enumerate(chunks, start=1)
        ]
        content.append({"type": "text", "text": last_user_text})

        api_messages = [{"role": m["role"], "content": m["content"]} for m in history]
        api_messages.append({"role": "user", "content": content})

        async with self._client.messages.stream(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            messages=api_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def identify_device(
        self, image_bytes: bytes, media_type: str
    ) -> DeviceIdentification:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        resp = await self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=VISION_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": VISION_INSTRUCTION},
                    ],
                }
            ],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        return parse_identification(text)
