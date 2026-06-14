"""Integration test for the pgvector retrieval path.

Requires a running Postgres+pgvector at DATABASE_URL with migrations applied:
    docker compose up -d && alembic upgrade head
Run with:  pytest -m pgvector
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Chunk, Device, Manual, ManualStatus

pytestmark = [pytest.mark.pgvector, pytest.mark.asyncio]


class _FixedQueryEmbedding:
    name = "fixed"
    model = "fixed"

    async def embed_query(self, text: str) -> list[float]:
        # Query vector closest to the "filter" chunk below.
        return [1.0, 0.0, 0.0]


@pytest.fixture
async def pg_session():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect():
            pass
    except Exception:  # pragma: no cover - environment guard
        pytest.skip("Postgres not reachable at DATABASE_URL")

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    async with maker() as cleanup:
        await cleanup.execute(delete(Device))  # cascades to manuals + chunks
        await cleanup.commit()
    await engine.dispose()


async def test_cosine_retrieval_orders_by_similarity(pg_session, monkeypatch):
    monkeypatch.setattr(
        "app.rag.retriever.get_embedding_provider", lambda s: _FixedQueryEmbedding()
    )
    from app.rag.retriever import retrieve

    device = Device(name="AC")
    pg_session.add(device)
    await pg_session.flush()

    manual = Manual(
        device_id=device.id,
        filename="ac.pdf",
        storage_key="x.pdf",
        content_type="application/pdf",
        size_bytes=1,
        status=ManualStatus.ready,
    )
    pg_session.add(manual)
    await pg_session.flush()

    near = Chunk(
        manual_id=manual.id, page=5, char_start=0, char_end=3, text="filter cleaning",
        token_count=1, embedding=[0.9, 0.1, 0.0],
    )
    far = Chunk(
        manual_id=manual.id, page=9, char_start=0, char_end=3, text="warranty terms",
        token_count=1, embedding=[0.0, 0.0, 1.0],
    )
    pg_session.add_all([near, far])
    await pg_session.commit()

    results = await retrieve(
        pg_session, get_settings(), query="how to clean filter",
        device_id=device.id, top_k=2,
    )
    assert [r.page for r in results] == [5, 9]  # nearest first
    assert results[0].text == "filter cleaning"


async def test_retrieval_skips_non_ready_manuals(pg_session, monkeypatch):
    monkeypatch.setattr(
        "app.rag.retriever.get_embedding_provider", lambda s: _FixedQueryEmbedding()
    )
    from app.rag.retriever import retrieve

    manual = Manual(
        filename="p.pdf", storage_key="p.pdf", content_type="application/pdf",
        size_bytes=1, status=ManualStatus.processing,
    )
    pg_session.add(manual)
    await pg_session.flush()
    pg_session.add(
        Chunk(manual_id=manual.id, page=1, char_start=0, char_end=1, text="t",
              token_count=1, embedding=[1.0, 0.0, 0.0])
    )
    await pg_session.commit()

    results = await retrieve(pg_session, get_settings(), query="anything", top_k=5)
    assert results == []
