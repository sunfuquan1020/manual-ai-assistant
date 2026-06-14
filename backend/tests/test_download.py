"""Tests for the QR-scan URL downloader and /manuals/from-url endpoint."""
from __future__ import annotations

import httpx
import pytest

from app.downloader import DownloadError, download_pdf

pytestmark = pytest.mark.asyncio


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_download_pdf_ok():
    def handler(_req):
        return httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=b"%PDF-1.4 body"
        )

    data, name = await download_pdf("http://x/manual.pdf", 1_000_000, client=_client(handler))
    assert data.startswith(b"%PDF")
    assert name == "manual.pdf"


async def test_download_derives_filename_when_path_has_none():
    def handler(_req):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF-x")

    _, name = await download_pdf("http://x/download?id=9", 1_000_000, client=_client(handler))
    assert name == "download.pdf"


async def test_download_rejects_non_pdf_content():
    def handler(_req):
        return httpx.Response(200, headers={"content-type": "text/html"}, content=b"<html>")

    with pytest.raises(DownloadError):
        await download_pdf("http://x/page", 1_000_000, client=_client(handler))


async def test_download_rejects_non_pdf_magic():
    def handler(_req):
        # Claims PDF but body is not a PDF.
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"<html>")

    with pytest.raises(DownloadError):
        await download_pdf("http://x/manual.pdf", 1_000_000, client=_client(handler))


async def test_download_enforces_size_limit():
    def handler(_req):
        return httpx.Response(200, headers={"content-type": "application/pdf"}, content=b"%PDF" + b"x" * 100)

    with pytest.raises(DownloadError):
        await download_pdf("http://x/manual.pdf", 10, client=_client(handler))


async def test_from_url_endpoint(client, monkeypatch):
    async def fake_download(url, max_bytes, http_client=None, **kwargs):
        return (b"%PDF-1.4", "ac.pdf")

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr("app.routers.manuals.download_pdf", fake_download)
    monkeypatch.setattr("app.routers.manuals.ingest_manual", noop)

    resp = await client.post(
        "/manuals/from-url",
        json={"url": "http://x/ac.pdf", "device_name": "客厅空调"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["filename"] == "ac.pdf"
    assert body["status"] == "pending"
    assert body["device_id"] is not None


async def test_from_url_rejects_bad_url(client, monkeypatch):
    async def fail(*args, **kwargs):
        raise DownloadError("URL is not a PDF (content-type=text/html)")

    monkeypatch.setattr("app.routers.manuals.download_pdf", fail)
    resp = await client.post("/manuals/from-url", json={"url": "http://x/page"})
    assert resp.status_code == 400
