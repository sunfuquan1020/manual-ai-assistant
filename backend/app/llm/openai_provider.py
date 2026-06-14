"""OpenAI provider — manual excerpts injected into the system prompt."""
from __future__ import annotations

from collections.abc import AsyncIterator

from ..rag.prompt import SYSTEM_PROMPT, format_context
from ..rag.retriever import RetrievedChunk
from .base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI

        self.model = model
        self._client = AsyncOpenAI(api_key=api_key)

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
