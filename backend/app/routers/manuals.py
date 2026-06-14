"""Manual upload & retrieval endpoints. (Ingest endpoint added in Stage 2.)"""
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
from ..embeddings.factory import embedding_provider_available
from ..ingest.pipeline import ingest_manual
from ..models import Device, Manual, ManualStatus
from ..schemas import ManualOut
from ..storage import get_storage

router = APIRouter(prefix="/manuals", tags=["manuals"])

_ALLOWED_CONTENT_TYPES = {"application/pdf"}


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

    # Resolve or create the owning device.
    resolved_device_id: uuid.UUID | None = None
    if device_id is not None:
        device = await session.get(Device, device_id)
        if device is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "device not found")
        resolved_device_id = device.id
    elif device_name:
        device = Device(name=device_name)
        session.add(device)
        await session.flush()
        resolved_device_id = device.id

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


@router.post("/{manual_id}/ingest", response_model=ManualOut)
async def ingest(
    manual_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> Manual:
    settings = get_settings()
    manual = await session.get(Manual, manual_id)
    if manual is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "manual not found")
    if manual.status == ManualStatus.processing:
        raise HTTPException(status.HTTP_409_CONFLICT, "ingest already in progress")

    # Validate the embedding provider up front so the client gets immediate feedback.
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
        ingest_manual, manual_id, get_sessionmaker(), get_storage(), settings
    )
    return manual


@router.get("/{manual_id}", response_model=ManualOut)
async def get_manual(
    manual_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> Manual:
    manual = await session.get(Manual, manual_id)
    if manual is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "manual not found")
    return manual
