"""Claude (Anthropic) provider — uses document blocks with native citations."""
from __future__ import annotations

from collections.abc import AsyncIterator

from ..rag.prompt import SYSTEM_PROMPT
from ..rag.retriever import RetrievedChunk
from .base import LLMProvider, Message


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str) -> None:
        import anthropic

        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

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
