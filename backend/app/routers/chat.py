"""RAG chat endpoint — SSE stream of answer deltas + a unified sources list.

SSE message shapes (one JSON object per ``data:`` frame, each carrying ``type``):
  {"type": "sources", "sources": [{chunk_id, manual_id, page, snippet}, ...]}
  {"type": "delta",   "text": "..."}
  {"type": "done"}
  {"type": "error",   "message": "..."}
"""
from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..embeddings.factory import EmbeddingNotConfiguredError
from ..llm.factory import LLMNotConfiguredError, get_llm_provider
from ..rag.retriever import RetrievedChunk, retrieve
from ..schemas import ChatRequest

router = APIRouter(tags=["chat"])

_SNIPPET_LEN = 240


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _sources_payload(chunks: list[RetrievedChunk]) -> dict:
    return {
        "type": "sources",
        "sources": [
            {
                "chunk_id": str(c.chunk_id),
                "manual_id": str(c.manual_id),
                "page": c.page,
                "snippet": c.text.strip()[:_SNIPPET_LEN],
            }
            for c in chunks
        ],
    }


@router.post("/chat")
async def chat(
    req: ChatRequest, session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    settings = get_settings()

    if req.messages[-1].role != "user":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "last message must have role 'user'"
        )

    # Resolve provider up front so misconfiguration returns a clean 400.
    try:
        provider = get_llm_provider(settings, req.provider, req.model)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    # Retrieve grounding chunks (DB used only here, before streaming begins).
    try:
        chunks = await retrieve(
            session,
            settings,
            query=req.messages[-1].content,
            device_id=req.device_id,
            manual_id=req.manual_id,
        )
    except EmbeddingNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    history = [{"role": m.role, "content": m.content} for m in req.messages]

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(_sources_payload(chunks))
        try:
            async for delta in provider.chat_stream(history, chunks):
                yield _sse({"type": "delta", "text": delta})
            yield _sse({"type": "done"})
        except Exception as exc:  # noqa: BLE001 — surface provider errors to the client
            yield _sse({"type": "error", "message": str(exc)[:500]})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
