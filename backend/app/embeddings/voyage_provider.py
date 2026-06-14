"""Voyage AI embeddings (Anthropic-recommended, multilingual)."""
from __future__ import annotations

import asyncio

from .base import EmbeddingProvider, InputType


class VoyageEmbeddingProvider(EmbeddingProvider):
    name = "voyage"

    def __init__(self, api_key: str, model: str) -> None:
        import voyageai

        self.model = model
        self._client = voyageai.Client(api_key=api_key)

    async def embed(
        self, texts: list[str], input_type: InputType = "document"
    ) -> list[list[float]]:
        if not texts:
            return []
        # voyageai client is sync; run off the event loop.
        result = await asyncio.to_thread(
            self._client.embed, texts, model=self.model, input_type=input_type
        )
        return result.embeddings
