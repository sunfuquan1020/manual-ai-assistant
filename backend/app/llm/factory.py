"""Select an LLM provider per chat request, falling back to configured defaults."""
from __future__ import annotations

from ..config import LLMProviderName, Settings
from .base import LLMProvider


class LLMNotConfiguredError(RuntimeError):
    pass


def llm_provider_available(name: LLMProviderName, settings: Settings) -> bool:
    if name == "claude":
        return bool(settings.anthropic_api_key)
    if name == "openai":
        return bool(settings.openai_api_key)
    if name == "ollama":
        return bool(settings.ollama_base_url)
    return False


def default_model_for(name: LLMProviderName, settings: Settings) -> str:
    return {
        "claude": settings.claude_model,
        "openai": settings.openai_model,
        "ollama": settings.ollama_model,
    }[name]


def get_llm_provider(
    settings: Settings,
    provider: LLMProviderName | None = None,
    model: str | None = None,
) -> LLMProvider:
    name = provider or settings.default_llm_provider
    if not llm_provider_available(name, settings):
        raise LLMNotConfiguredError(f"LLM provider {name!r} is not configured")
    chosen_model = model or default_model_for(name, settings)

    if name == "claude":
        from .claude_provider import ClaudeProvider

        return ClaudeProvider(settings.anthropic_api_key, chosen_model)
    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(settings.openai_api_key, chosen_model)
    if name == "ollama":
        from .ollama_provider import OllamaProvider

        return OllamaProvider(settings.ollama_base_url, chosen_model)
    raise LLMNotConfiguredError(f"unknown LLM provider {name!r}")
