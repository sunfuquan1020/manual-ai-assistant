"""Tests for photo-based device identification (vision provider stubbed)."""
from __future__ import annotations

import pytest

from app.llm.base import DeviceIdentification, LLMProvider

pytestmark = pytest.mark.asyncio


class _FakeVision(LLMProvider):
    name = "fake"
    model = "fake"

    async def chat_stream(self, messages, chunks):
        if False:  # pragma: no cover - present only to satisfy the abstract method
            yield ""

    async def identify_device(self, image_bytes, media_type):
        return DeviceIdentification(
            brand="Gree",
            model_number="KFR-35",
            category="空调",
            device_type="壁挂空调",
            keywords=["空调", "格力"],
        )


async def test_identify_matches_existing_device(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.devices.get_llm_provider", lambda *a, **k: _FakeVision()
    )
    await client.post("/devices", json={"name": "客厅空调", "brand": "Gree"})

    resp = await client.post(
        "/devices/identify",
        files={"file": ("photo.jpg", b"\xff\xd8\xff\xe0fakejpeg", "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["identification"]["category"] == "空调"
    assert body["identification"]["keywords"] == ["空调", "格力"]
    names = [m["device"]["name"] for m in body["matches"]]
    assert "客厅空调" in names


async def test_identify_rejects_non_image(client):
    resp = await client.post(
        "/devices/identify",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415


async def test_identify_rejects_unconfigured_provider(client):
    # provider=claude with no ANTHROPIC_API_KEY in test env → 400
    resp = await client.post(
        "/devices/identify",
        files={"file": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
        data={"provider": "claude"},
    )
    assert resp.status_code == 400
