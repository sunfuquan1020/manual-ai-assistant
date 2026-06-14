"""Stage 1 integration tests for the manual upload endpoint."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_upload_pdf_succeeds(client, sample_pdf_bytes):
    resp = await client.post(
        "/manuals/upload",
        files={"file": ("fridge.pdf", sample_pdf_bytes, "application/pdf")},
        data={"device_name": "Fridge"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["filename"] == "fridge.pdf"
    assert body["status"] == "pending"
    assert body["device_id"] is not None
    assert body["size_bytes"] == len(sample_pdf_bytes)


async def test_upload_rejects_non_pdf(client):
    resp = await client.post(
        "/manuals/upload",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 415


async def test_upload_rejects_empty_file(client):
    resp = await client.post(
        "/manuals/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert resp.status_code == 400


async def test_get_manual_roundtrip(client, sample_pdf_bytes):
    up = await client.post(
        "/manuals/upload",
        files={"file": ("ac.pdf", sample_pdf_bytes, "application/pdf")},
    )
    manual_id = up.json()["id"]
    got = await client.get(f"/manuals/{manual_id}")
    assert got.status_code == 200
    assert got.json()["id"] == manual_id
