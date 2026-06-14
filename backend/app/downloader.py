"""Download a manual PDF from a URL (used by the QR-scan flow).

Streams with a hard size cap and validates that the response is actually a PDF
before we store it. Many appliance QR codes encode a direct PDF link; pages that
return HTML are rejected with a clear error.
"""
from __future__ import annotations

import os
from urllib.parse import unquote, urlparse

import httpx


class DownloadError(RuntimeError):
    pass


async def download_pdf(
    url: str, max_bytes: int, client: httpx.AsyncClient | None = None
) -> tuple[bytes, str]:
    """Return (pdf_bytes, filename). Raises DownloadError on any problem.

    ``client`` may be injected for testing (e.g. with an httpx MockTransport);
    when omitted a default client is created and closed.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise DownloadError("only http/https URLs are supported")

    owns_client = client is None
    http = client or httpx.AsyncClient(follow_redirects=True, timeout=30.0)
    try:
        async with http.stream("GET", url) as resp:
            if resp.status_code != 200:
                raise DownloadError(f"download failed: HTTP {resp.status_code}")

            content_type = resp.headers.get("content-type", "").lower()
            path_is_pdf = parsed.path.lower().endswith(".pdf")
            if "application/pdf" not in content_type and not path_is_pdf:
                raise DownloadError(
                    f"URL is not a PDF (content-type={content_type or 'unknown'})"
                )

            chunks: list[bytes] = []
            total = 0
            async for chunk in resp.aiter_bytes():
                total += len(chunk)
                if total > max_bytes:
                    raise DownloadError("file exceeds size limit")
                chunks.append(chunk)
    except httpx.HTTPError as exc:
        raise DownloadError(f"network error: {exc}") from exc
    finally:
        if owns_client:
            await http.aclose()

    data = b"".join(chunks)
    if not data:
        raise DownloadError("empty download")
    if not data.startswith(b"%PDF"):
        raise DownloadError("downloaded content is not a valid PDF")

    name = os.path.basename(unquote(parsed.path)) or "manual.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return data, name
