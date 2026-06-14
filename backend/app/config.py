"""Application configuration loaded from environment / .env.

Secrets for every LLM/embedding provider live here and are read only on the
backend — the Android app never receives any key, only provider/model names.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProviderName = Literal["claude", "openai", "ollama"]
EmbeddingProviderName = Literal["voyage", "openai", "ollama"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    database_url: str = "postgresql+psycopg://manuals:manuals@localhost:5432/manuals"

    # Storage
    storage_dir: str = "./_storage"
    max_upload_mb: int = 50

    # Provider defaults
    default_llm_provider: LLMProviderName = "claude"
    default_embedding_provider: EmbeddingProviderName = "voyage"

    # Claude
    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-4-8"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1"
    openai_embedding_model: str = "text-embedding-3-small"

    # Voyage
    voyage_api_key: str | None = None
    voyage_embedding_model: str = "voyage-3"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"

    # Retrieval / chunking
    rag_top_k: int = 6
    chunk_tokens: int = 500
    chunk_overlap_tokens: int = 80

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_startup(settings: Settings) -> None:
    """Fail fast if the *default* providers are missing required credentials.

    Non-default providers are validated lazily when a request selects them, so
    an operator can run with only one provider configured.
    """
    missing: list[str] = []

    if settings.default_llm_provider == "claude" and not settings.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY (default_llm_provider=claude)")
    if settings.default_llm_provider == "openai" and not settings.openai_api_key:
        missing.append("OPENAI_API_KEY (default_llm_provider=openai)")

    if settings.default_embedding_provider == "voyage" and not settings.voyage_api_key:
        missing.append("VOYAGE_API_KEY (default_embedding_provider=voyage)")
    if settings.default_embedding_provider == "openai" and not settings.openai_api_key:
        missing.append("OPENAI_API_KEY (default_embedding_provider=openai)")

    # Ollama needs only a reachable base_url, which always has a default.

    if missing:
        raise RuntimeError(
            "Missing required configuration for default providers: "
            + ", ".join(missing)
        )
