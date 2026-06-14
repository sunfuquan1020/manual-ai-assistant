"""Stage 3 tests for the providers listing endpoint."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_list_providers(client):
    resp = await client.get("/providers")
    assert resp.status_code == 200
    by_name = {p["provider"]: p for p in resp.json()}
    assert set(by_name) == {"claude", "openai", "ollama"}
    # Ollama needs only a base_url (defaulted), so it is available in tests.
    assert by_name["ollama"]["available"] is True
    # No ANTHROPIC_API_KEY / OPENAI_API_KEY in the test env.
    assert by_name["claude"]["available"] is False
    assert by_name["openai"]["available"] is False
    # The configured default model is always present in the list.
    assert by_name["claude"]["default_model"] in by_name["claude"]["models"]
