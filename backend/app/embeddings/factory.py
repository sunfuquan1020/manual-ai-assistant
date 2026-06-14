"""Select the (global) embedding provider from settings.

Embedding provider is global, not per-request: every chunk in the knowledge base
must share one embedding model so vector dimensions match. Switching providers
requires re-ingesting manuals.
"""
from __future__ import annotations

from ..config import EmbeddingProviderName, Settings
from .base import EmbeddingProvider


class EmbeddingNotConfiguredError(RuntimeError):
    pass


def embedding_provider_available(name: EmbeddingProviderName, settings: Settings) -> bool:
    if name == "voyage":
        return bool(settings.voyage_api_key)
    if name == "openai":
        return bool(settings.openai_api_key)
    if name == "ollama":
        return bool(settings.ollama_base_url)
    return False


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    name = settings.default_embedding_provider
    if not embedding_provider_available(name, settings):
        raise EmbeddingNotConfiguredError(
            f"embedding provider {name!r} is not configured"
        )

    if name == "voyage":
        from .voyage_provider import VoyageEmbeddingProvider

        return VoyageEmbeddingProvider(
            settings.voyage_api_key, settings.voyage_embedding_model
        )
    if name == "openai":
        from .openai_provider import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            settings.openai_api_key, settings.openai_embedding_model
        )
    if name == "ollama":
        from .ollama_provider import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(
            settings.ollama_base_url, settings.ollama_embedding_model
        )
    raise EmbeddingNotConfiguredError(f"unknown embedding provider {name!r}")
