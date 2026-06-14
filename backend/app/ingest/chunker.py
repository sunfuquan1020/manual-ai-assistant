"""Split page text into overlapping chunks for embedding.

Chunks are page-scoped: every chunk belongs to exactly one page, so the page
number stored on the chunk is an exact citation. Token counts use a lightweight
~4-chars-per-token estimate (deliberately provider-agnostic — we are sizing
chunks, not billing tokens, so a precise tokenizer is unnecessary).
"""
from __future__ import annotations

from dataclasses import dataclass

from .pdf_parser import PageText

_CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class ChunkData:
    page: int
    char_start: int
    char_end: int
    text: str
    token_count: int


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN)


def chunk_pages(
    pages: list[PageText], chunk_tokens: int, overlap_tokens: int
) -> list[ChunkData]:
    window = max(1, chunk_tokens * _CHARS_PER_TOKEN)
    overlap = max(0, min(overlap_tokens, chunk_tokens - 1) * _CHARS_PER_TOKEN)
    step = max(1, window - overlap)

    chunks: list[ChunkData] = []
    for page in pages:
        text = page.text
        n = len(text)
        if n <= window:
            chunks.append(
                ChunkData(page.page, 0, n, text, estimate_tokens(text))
            )
            continue
        start = 0
        while start < n:
            end = min(start + window, n)
            segment = text[start:end]
            chunks.append(
                ChunkData(page.page, start, end, segment, estimate_tokens(segment))
            )
            if end >= n:
                break
            start += step
    return chunks
