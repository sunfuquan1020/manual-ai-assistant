"""Unit tests for embedder batching and provider factory selection."""
from __future__ import annotations

import pytest

from app.config import Settings
from app.embeddings.base import EmbeddingProvider, InputType
from app.ingest.embedder import embed_documents
from app.embeddings.factory import (
    EmbeddingNotConfiguredError,
    embedding_provider_available,
    get_embedding_provider,
)


class _FakeProvider(EmbeddingProvider):
    name = "fake"
    model = "fake-model"

    async def embed(
        self, texts: list[str], input_type: InputType = "document"
    ) -> list[list[float]]:
        return [[float(len(t)), 1.0] for t in texts]


@pytest.mark.asyncio
async def test_embed_documents_preserves_order_and_count():
    texts = [f"item-{i}" + "x" * i for i in range(250)]  # spans multiple batches
    vectors = await embed_documents(_FakeProvider(), texts)
    assert len(vectors) == len(texts)
    assert vectors[5][0] == float(len(texts[5]))


def test_voyage_unconfigured_is_unavailable():
    s = Settings(default_embedding_provider="voyage", voyage_api_key=None)
    assert embedding_provider_available("voyage", s) is False
    with pytest.raises(EmbeddingNotConfiguredError):
        get_embedding_provider(s)


def test_ollama_available_without_api_key():
    s = Settings(default_embedding_provider="ollama")
    assert embedding_provider_available("ollama", s) is True
    provider = get_embedding_provider(s)
    assert provider.name == "ollama"
