"""Unit tests for page-scoped chunking."""
from __future__ import annotations

from app.ingest.chunker import chunk_pages, estimate_tokens
from app.ingest.pdf_parser import PageText


def test_short_page_is_single_chunk():
    pages = [PageText(page=3, text="short text")]
    chunks = chunk_pages(pages, chunk_tokens=500, overlap_tokens=80)
    assert len(chunks) == 1
    assert chunks[0].page == 3
    assert chunks[0].char_start == 0
    assert chunks[0].char_end == len("short text")
    assert chunks[0].text == "short text"


def test_long_page_splits_with_overlap_and_stays_on_page():
    text = "A" * 100
    pages = [PageText(page=7, text=text)]
    # window = chunk_tokens*4 = 8, overlap = 1*4 = 4, step = 8 - 4 = 4
    chunks = chunk_pages(pages, chunk_tokens=2, overlap_tokens=1)
    assert len(chunks) > 1
    assert all(c.page == 7 for c in chunks)
    assert chunks[0].char_start == 0
    assert chunks[1].char_start == 4  # step
    # full coverage: last chunk reaches end
    assert chunks[-1].char_end == 100


def test_each_chunk_maps_to_one_page():
    pages = [PageText(page=1, text="x" * 50), PageText(page=2, text="y" * 50)]
    chunks = chunk_pages(pages, chunk_tokens=5, overlap_tokens=1)
    pages_seen = {c.page for c in chunks}
    assert pages_seen == {1, 2}


def test_estimate_tokens_nonzero():
    assert estimate_tokens("") == 1
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 9) == 3
