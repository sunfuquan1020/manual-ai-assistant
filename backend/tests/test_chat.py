"""Stage 3 tests for the /chat SSE endpoint (retriever + LLM provider stubbed)."""
from __future__ import annotations

import json
import uuid

import pytest

from app.rag.retriever import RetrievedChunk

pytestmark = pytest.mark.asyncio


class _FakeLLM:
    name = "fake"
    model = "fake-model"

    async def chat_stream(self, messages, chunks):
        # Echo that we received grounding + the question, in two deltas.
        yield f"基于{len(chunks)}条来源："
        yield messages[-1]["content"][::-1]


def _parse_sse(text: str) -> list[dict]:
    events = []
    for block in text.strip().split("\n\n"):
        line = block.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:") :].strip()))
    return events


async def test_chat_streams_sources_deltas_done(client, monkeypatch):
    fake_chunk = RetrievedChunk(
        chunk_id=uuid.uuid4(),
        manual_id=uuid.uuid4(),
        page=12,
        text="清洗滤网：取出滤网用清水冲洗。",
    )

    async def fake_retrieve(*args, **kwargs):
        return [fake_chunk]

    monkeypatch.setattr("app.routers.chat.retrieve", fake_retrieve)
    monkeypatch.setattr(
        "app.routers.chat.get_llm_provider", lambda *a, **k: _FakeLLM()
    )

    resp = await client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "滤网怎么清洗"}],
            "provider": "ollama",
        },
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    types = [e["type"] for e in events]
    assert types[0] == "sources"
    assert "delta" in types
    assert types[-1] == "done"

    sources = events[0]["sources"]
    assert sources[0]["page"] == 12
    assert sources[0]["manual_id"] == str(fake_chunk.manual_id)


async def test_chat_rejects_unconfigured_provider(client):
    # No ANTHROPIC_API_KEY in the test env → claude is unavailable → 400.
    resp = await client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "provider": "claude",
        },
    )
    assert resp.status_code == 400


async def test_chat_requires_trailing_user_message(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.chat.get_llm_provider", lambda *a, **k: _FakeLLM()
    )

    async def fake_retrieve(*args, **kwargs):
        return []

    monkeypatch.setattr("app.routers.chat.retrieve", fake_retrieve)

    resp = await client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
            "provider": "ollama",
        },
    )
    assert resp.status_code == 400
