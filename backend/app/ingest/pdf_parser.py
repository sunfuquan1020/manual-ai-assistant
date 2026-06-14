"""Extract per-page text from a PDF using PyMuPDF.

Page numbers are 1-based so they map directly to what a user sees in the manual.
Scanned/image-only PDFs yield empty text here; OCR fallback is a later phase.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


def parse_pdf(data: bytes) -> list[PageText]:
    import fitz  # PyMuPDF

    pages: list[PageText] = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(PageText(page=index, text=text))
    return pages
