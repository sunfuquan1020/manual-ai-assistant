"""Batch-embed chunk texts via the configured EmbeddingProvider."""
from __future__ import annotations

from ..embeddings.base import EmbeddingProvider

_BATCH = 96


async def embed_documents(
    provider: EmbeddingProvider, texts: list[str]
) -> list[list[float]]:
    vectors: list[list[float]] = []
    for i in range(0, len(texts), _BATCH):
        batch = texts[i : i + _BATCH]
        vectors.extend(await provider.embed(batch, input_type="document"))
    return vectors
