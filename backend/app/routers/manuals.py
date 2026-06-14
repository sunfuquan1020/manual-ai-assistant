"""Manual upload, URL-download (QR scan), ingest & retrieval endpoints."""
from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session, get_sessionmaker
from ..downloader import DownloadError, download_pdf
from ..embeddings.factory import embedding_provider_available
from ..ingest.pipeline import ingest_manual
from ..models import Device, Manual, ManualStatus
from ..schemas import ManualFromUrlBody, ManualOut
from ..storage import get_storage

router = APIRouter(prefix="/manuals", tags=["manuals"])

_ALLOWED_CONTENT_TYPES = {"application/pdf"}


async def _resolve_device(
    session: AsyncSession, device_id: uuid.UUID | None, device_name: str | None
) -> uuid.UUID | None:
    if device_id is not None:
        device = await session.get(Device, device_id)
        if device is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "device not found")
        return device.id
    if device_name:
        device = Device(name=device_name)
        session.add(device)
        await session.flush()
        return device.id
    return None


async def _start_ingest(
    session: AsyncSession, manual: Manual, background_tasks: BackgroundTasks
) -> None:
    """Validate the embedding provider, mark pending, and schedule ingestion."""
    settings = get_settings()
    if not embedding_provider_available(settings.default_embedding_provider, settings):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"embedding provider {settings.default_embedding_provider!r} is not configured",
        )
    manual.status = ManualStatus.pending
    manual.error = None
    await session.commit()
    await session.refresh(manual)
    background_tasks.add_task(
        ingest_manual, manual.id, get_sessionmaker(), get_storage(), settings
    )


@router.post("/upload", response_model=ManualOut, status_code=status.HTTP_201_CREATED)
async def upload_manual(
    file: UploadFile = File(...),
    device_id: uuid.UUID | None = Form(default=None),
    device_name: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> Manual:
    settings = get_settings()

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"only PDF is supported, got {file.content_type!r}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty file")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"file exceeds {settings.max_upload_mb} MB limit",
        )

    resolved_device_id = await _resolve_device(session, device_id, device_name)
    storage = get_storage()
    key = storage.put(data, file.filename or "manual.pdf")

    manual = Manual(
        device_id=resolved_device_id,
        filename=file.filename or "manual.pdf",
        storage_key=key,
        content_type=file.content_type,
        size_bytes=len(data),
        status=ManualStatus.pending,
    )
    session.add(manual)
    await session.commit()
    await session.refresh(manual)
    return manual


@router.post("/from-url", response_model=ManualOut, status_code=status.HTTP_201_CREATED)
async def manual_from_url(
    body: ManualFromUrlBody,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Manual:
    """Download a PDF manual from a (QR-scanned) URL, store it, and start ingestion."""
    settings = get_settings()
    try:
        data, filename = await download_pdf(body.url, settings.max_upload_bytes)
    except DownloadError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    resolved_device_id = await _resolve_device(session, body.device_id, body.device_name)
    storage = get_storage()
    key = storage.put(data, filename)

    manual = Manual(
        device_id=resolved_device_id,
        filename=filename,
        storage_key=key,
        content_type="application/pdf",
        size_bytes=len(data),
        status=ManualStatus.pending,
    )
    session.add(manual)
    await session.commit()
    await session.refresh(manual)

    # Auto-ingest after a URL download (one-tap UX for the scan flow).
    await _start_ingest(session, manual, background_tasks)
    return manual


@router.post("/{manual_id}/ingest", response_model=ManualOut)
async def ingest(
    manual_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Manual:
    manual = await session.get(Manual, manual_id)
    if manual is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "manual not found")
    if manual.status == ManualStatus.processing:
        raise HTTPException(status.HTTP_409_CONFLICT, "ingest already in progress")
    await _start_ingest(session, manual, background_tasks)
    return manual


@router.get("/{manual_id}", response_model=ManualOut)
async def get_manual(
    manual_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> Manual:
    manual = await session.get(Manual, manual_id)
    if manual is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "manual not found")
    return manual
