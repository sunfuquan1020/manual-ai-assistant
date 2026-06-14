"""Embedding provider abstraction.

All providers return plain ``list[float]`` vectors. ``input_type`` lets providers
that distinguish document vs query embeddings (e.g. Voyage) optimize retrieval;
providers that don't care simply ignore it.
"""
from __future__ import annotations

import abc
from typing import Literal

InputType = Literal["document", "query"]


class EmbeddingProvider(abc.ABC):
    name: str
    model: str

    @abc.abstractmethod
    async def embed(
        self, texts: list[str], input_type: InputType = "document"
    ) -> list[list[float]]:
        ...

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed([text], input_type="query")
        return vectors[0]
