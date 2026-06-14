"""LLM provider abstraction.

A provider receives the conversation history plus retrieved manual chunks and
streams back answer text deltas. Source attribution is emitted uniformly by the
chat router from the retrieved chunks, so providers only stream generation; this
keeps the SSE contract identical regardless of which provider is selected.
"""
from __future__ import annotations

import abc
from collections.abc import AsyncIterator

from ..rag.retriever import RetrievedChunk

# A conversation message: {"role": "user"|"assistant", "content": str}
Message = dict[str, str]


class LLMProvider(abc.ABC):
    name: str
    model: str

    @abc.abstractmethod
    def chat_stream(
        self, messages: list[Message], chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        """Yield answer text deltas. Must be an async generator."""
        ...
