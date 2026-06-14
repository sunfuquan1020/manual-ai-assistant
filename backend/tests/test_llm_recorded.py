"""Recorded/replay integration tests for the LLM providers.

Each provider's HTTP layer is replaced with an httpx MockTransport that replays a
recorded response from ``tests/cassettes/``. This exercises the real provider
code (SDK request building + streaming response parsing) fully offline and
deterministically — no API keys, no network.

To re-record against a live API: capture the raw streaming HTTP body for the
provider and overwrite the matching cassette file, keeping the wire format.
"""
from __future__ import annotations

import pathlib

import httpx
import pytest

pytestmark = [pytest.mark.recorded, pytest.mark.asyncio]

_CASSETTES = pathlib.Path(__file__).parent / "cassettes"


def _replay_client(filename: str, content_type: str) -> httpx.AsyncClient:
    body = (_CASSETTES / filename).read_bytes()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": content_type}, content=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def _collect(provider) -> str:
    deltas = [
        d
        async for d in provider.chat_stream(
            [{"role": "user", "content": "滤网怎么清洗"}], []
        )
    ]
    return "".join(deltas)


async def test_claude_chat_replay():
    from app.llm.claude_provider import ClaudeProvider

    client = _replay_client("claude_chat.sse", "text/event-stream")
    provider = ClaudeProvider("test-key", "claude-opus-4-8", http_client=client)
    assert await _collect(provider) == "取出滤网，用清水冲洗即可。"


async def test_openai_chat_replay():
    from app.llm.openai_provider import OpenAIProvider

    client = _replay_client("openai_chat.sse", "text/event-stream")
    provider = OpenAIProvider("test-key", "gpt-4.1", http_client=client)
    assert await _collect(provider) == "Remove the filter and rinse it under water."


async def test_ollama_chat_replay():
    from app.llm.ollama_provider import OllamaProvider

    client = _replay_client("ollama_chat.ndjson", "application/x-ndjson")
    provider = OllamaProvider("http://localhost:11434", "llama3.1", http_client=client)
    assert await _collect(provider) == "取出滤网，用清水冲洗。"


# ---- Vision / device identification replays ----

def _assert_gree(ident) -> None:
    assert ident.brand == "Gree"
    assert ident.category == "空调"
    assert ident.keywords == ["空调", "格力"]


async def test_claude_identify_replay():
    from app.llm.claude_provider import ClaudeProvider

    client = _replay_client("claude_identify.json", "application/json")
    provider = ClaudeProvider("test-key", "claude-opus-4-8", http_client=client)
    _assert_gree(await provider.identify_device(b"\xff\xd8\xff", "image/jpeg"))


async def test_openai_identify_replay():
    from app.llm.openai_provider import OpenAIProvider

    client = _replay_client("openai_identify.json", "application/json")
    provider = OpenAIProvider("test-key", "gpt-4.1", http_client=client)
    _assert_gree(await provider.identify_device(b"\xff\xd8\xff", "image/jpeg"))


async def test_ollama_identify_replay():
    from app.llm.ollama_provider import OllamaProvider

    client = _replay_client("ollama_identify.json", "application/json")
    provider = OllamaProvider("http://localhost:11434", "llava", http_client=client)
    _assert_gree(await provider.identify_device(b"\xff\xd8\xff", "image/jpeg"))
