"""OpenAI provider — manual excerpts injected into the system prompt."""
from __future__ import annotations

import base64
from collections.abc import AsyncIterator

from ..rag.prompt import SYSTEM_PROMPT, format_context
from ..rag.retriever import RetrievedChunk
from .base import DeviceIdentification, LLMProvider, Message
from .vision import VISION_INSTRUCTION, VISION_SYSTEM, parse_identification


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, http_client=None) -> None:
        from openai import AsyncOpenAI

        self.model = model
        # http_client is injectable for recorded/replay tests (httpx MockTransport).
        self._client = AsyncOpenAI(api_key=api_key, http_client=http_client)

    async def chat_stream(
        self, messages: list[Message], chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        system = (
            SYSTEM_PROMPT
            + "\n\n说明书摘录 / Manual excerpts:\n"
            + format_context(chunks)
        )
        api_messages = [{"role": "system", "content": system}, *messages]

        stream = await self._client.chat.completions.create(
            model=self.model, messages=api_messages, stream=True
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def identify_device(
        self, image_bytes: bytes, media_type: str
    ) -> DeviceIdentification:
        b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        resp = await self._client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": VISION_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_INSTRUCTION},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{b64}"},
                        },
                    ],
                },
            ],
        )
        text = resp.choices[0].message.content or ""
        return parse_identification(text)
