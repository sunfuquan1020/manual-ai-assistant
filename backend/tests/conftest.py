"""Shared test fixtures.

Upload-path tests only touch the ``devices`` and ``manuals`` tables, so they run
against SQLite (the ``chunks.embedding`` pgvector column is never created here).
RAG/ingest tests that need pgvector are marked and require Postgres.
"""
from __future__ import annotations

import os
import tempfile

# Configure environment BEFORE importing the app (settings are cached).
_TMP = tempfile.mkdtemp(prefix="manuals-test-")
os.environ.setdefault("STORAGE_DIR", os.path.join(_TMP, "storage"))
os.environ.setdefault("DEFAULT_LLM_PROVIDER", "ollama")
os.environ.setdefault("DEFAULT_EMBEDDING_PROVIDER", "ollama")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session
from app.main import app
from app.models import Device, Manual


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # Create only the non-vector tables for upload tests.
        await conn.run_sync(
            lambda c: Device.__table__.create(c, checkfirst=True)
        )
        await conn.run_sync(
            lambda c: Manual.__table__.create(c, checkfirst=True)
        )

    testing_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _override():
        async with testing_session() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    # Minimal valid-enough PDF header; upload path does not parse it.
    return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
