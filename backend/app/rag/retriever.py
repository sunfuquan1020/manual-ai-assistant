"""Vector retrieval over manual chunks (pgvector cosine distance).

The query is embedded with the *global* embedding provider — the same one used
at ingest time — so dimensions match. Brute-force cosine ordering is fine at
family scale; an ANN index can be added later without API changes.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..embeddings.factory import get_embedding_provider
from ..models import Chunk, Manual, ManualStatus


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    manual_id: uuid.UUID
    page: int
    text: str


async def retrieve(
    session: AsyncSession,
    settings: Settings,
    query: str,
    *,
    device_id: uuid.UUID | None = None,
    manual_id: uuid.UUID | None = None,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    k = top_k or settings.rag_top_k
    provider = get_embedding_provider(settings)
    query_vec = await provider.embed_query(query)

    stmt = (
        select(Chunk)
        .join(Manual, Manual.id == Chunk.manual_id)
        .where(Manual.status == ManualStatus.ready)
    )
    if manual_id is not None:
        stmt = stmt.where(Chunk.manual_id == manual_id)
    elif device_id is not None:
        stmt = stmt.where(Manual.device_id == device_id)

    stmt = stmt.order_by(Chunk.embedding.cosine_distance(query_vec)).limit(k)

    result = await session.execute(stmt)
    return [
        RetrievedChunk(
            chunk_id=c.id, manual_id=c.manual_id, page=c.page, text=c.text
        )
        for c in result.scalars().all()
    ]
