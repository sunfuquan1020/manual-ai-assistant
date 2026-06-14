"""Expose configured LLM providers + suggested models for the app settings page."""
from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings
from ..llm.factory import default_model_for, llm_provider_available
from ..schemas import ProviderModelInfo

router = APIRouter(prefix="/providers", tags=["providers"])

# Suggested models per provider (the configured default is always included).
_SUGGESTED: dict[str, list[str]] = {
    "claude": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"],
    "openai": ["gpt-4.1", "gpt-4.1-mini", "gpt-4o"],
    "ollama": ["llama3.1", "qwen2.5", "gemma2"],
}


@router.get("", response_model=list[ProviderModelInfo])
async def list_providers() -> list[ProviderModelInfo]:
    settings = get_settings()
    out: list[ProviderModelInfo] = []
    for name in ("claude", "openai", "ollama"):
        default = default_model_for(name, settings)  # type: ignore[arg-type]
        models = list(dict.fromkeys([default, *_SUGGESTED.get(name, [])]))
        out.append(
            ProviderModelInfo(
                provider=name,
                available=llm_provider_available(name, settings),  # type: ignore[arg-type]
                default_model=default,
                models=models,
            )
        )
    return out
