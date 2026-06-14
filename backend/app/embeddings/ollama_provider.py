"""Ollama embeddings (local or cloud) via the /api/embed endpoint."""
from __future__ import annotations

import httpx

from .base import EmbeddingProvider, InputType


class OllamaEmbeddingProvider(EmbeddingProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self.model = model
        self._base_url = base_url.rstrip("/")

    async def embed(
        self, texts: list[str], input_type: InputType = "document"
    ) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": self.model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
        return data["embeddings"]
