"""LLM provider abstraction.

A provider receives the conversation history plus retrieved manual chunks and
streams back answer text deltas. Source attribution is emitted uniformly by the
chat router from the retrieved chunks, so providers only stream generation; this
keeps the SSE contract identical regardless of which provider is selected.
"""
from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from ..rag.retriever import RetrievedChunk

# A conversation message: {"role": "user"|"assistant", "content": str}
Message = dict[str, str]


@dataclass
class DeviceIdentification:
    """Structured result of identifying an appliance from a photo."""

    brand: str | None = None
    model_number: str | None = None
    category: str | None = None
    device_type: str | None = None
    keywords: list[str] = field(default_factory=list)
    raw: str = ""


class LLMProvider(abc.ABC):
    name: str
    model: str

    @abc.abstractmethod
    def chat_stream(
        self, messages: list[Message], chunks: list[RetrievedChunk]
    ) -> AsyncIterator[str]:
        """Yield answer text deltas. Must be an async generator."""
        ...

    async def identify_device(
        self, image_bytes: bytes, media_type: str
    ) -> DeviceIdentification:
        """Identify an appliance from a photo. Override in vision-capable providers."""
        raise NotImplementedError(f"{self.name} does not support image identification")
