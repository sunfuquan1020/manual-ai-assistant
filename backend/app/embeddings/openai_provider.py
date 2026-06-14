"""OpenAI embeddings (text-embedding-3-*)."""
from __future__ import annotations

from .base import EmbeddingProvider, InputType


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        from openai import AsyncOpenAI

        self.model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def embed(
        self, texts: list[str], input_type: InputType = "document"
    ) -> list[list[float]]:
        if not texts:
            return []
        resp = await self._client.embeddings.create(model=self.model, input=texts)
        # Preserve request order.
        return [item.embedding for item in sorted(resp.data, key=lambda d: d.index)]
