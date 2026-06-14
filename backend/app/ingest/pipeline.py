"""Ingest orchestration: parse → chunk → embed → store.

Runs as a background task with its own DB session (the request session is gone
by the time this executes). On any failure the manual is marked ``failed`` with
the error message so the client can surface it.
"""
from __future__ import annotations

import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..embeddings.factory import get_embedding_provider
from ..models import Chunk, Manual, ManualStatus
from ..storage import LocalStorage
from .chunker import chunk_pages
from .embedder import embed_documents
from .pdf_parser import parse_pdf


async def ingest_manual(
    manual_id: uuid.UUID,
    sessionmaker: async_sessionmaker,
    storage: LocalStorage,
    settings: Settings,
) -> None:
    async with sessionmaker() as session:
        manual = await session.get(Manual, manual_id)
        if manual is None:
            return
        manual.status = ManualStatus.processing
        manual.error = None
        await session.commit()

        try:
            data = storage.read(manual.storage_key)
            pages = parse_pdf(data)
            if not pages:
                raise ValueError(
                    "no extractable text (scanned PDF? OCR is a later phase)"
                )

            chunk_data = chunk_pages(
                pages, settings.chunk_tokens, settings.chunk_overlap_tokens
            )
            provider = get_embedding_provider(settings)
            vectors = await embed_documents(provider, [c.text for c in chunk_data])

            # Replace any previous chunks (idempotent re-ingest).
            await session.execute(delete(Chunk).where(Chunk.manual_id == manual_id))
            session.add_all(
                [
                    Chunk(
                        manual_id=manual_id,
                        page=c.page,
                        char_start=c.char_start,
                        char_end=c.char_end,
                        text=c.text,
                        token_count=c.token_count,
                        embedding=vec,
                    )
                    for c, vec in zip(chunk_data, vectors)
                ]
            )

            manual.status = ManualStatus.ready
            manual.page_count = pages[-1].page
            manual.embedding_model = provider.model
            manual.embedding_dim = len(vectors[0]) if vectors else None
            manual.error = None
            await session.commit()
        except Exception as exc:  # noqa: BLE001 — record any failure for the client
            await session.rollback()
            manual = await session.get(Manual, manual_id)
            if manual is not None:
                manual.status = ManualStatus.failed
                manual.error = str(exc)[:1000]
                await session.commit()
