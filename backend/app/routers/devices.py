"""Device endpoints, including photo-based identification."""
from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import LLMProviderName, get_settings
from ..db import get_session
from ..llm.factory import LLMNotConfiguredError, get_llm_provider
from ..models import Device, Manual, ManualStatus
from ..schemas import (
    DeviceCreate,
    DeviceMatchOut,
    DeviceOut,
    IdentificationOut,
    IdentifyResponse,
    ManualOut,
)

router = APIRouter(prefix="/devices", tags=["devices"])


async def _match_devices(
    session: AsyncSession, terms: list[str]
) -> list[DeviceMatchOut]:
    cleaned = [t.strip() for t in terms if t and t.strip()]
    if not cleaned:
        return []
    conditions = []
    for t in cleaned:
        like = f"%{t}%"
        conditions += [
            Device.name.ilike(like),
            Device.brand.ilike(like),
            Device.category.ilike(like),
            Device.model_number.ilike(like),
        ]
    result = await session.execute(select(Device).where(or_(*conditions)).limit(10))
    devices = list(result.scalars().all())

    matches: list[DeviceMatchOut] = []
    for device in devices:
        manuals_result = await session.execute(
            select(Manual)
            .where(Manual.device_id == device.id, Manual.status == ManualStatus.ready)
            .order_by(Manual.created_at.desc())
        )
        manuals = list(manuals_result.scalars().all())
        matches.append(
            DeviceMatchOut(
                device=DeviceOut.model_validate(device),
                manuals=[ManualOut.model_validate(m) for m in manuals],
            )
        )
    return matches


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate, session: AsyncSession = Depends(get_session)
) -> Device:
    device = Device(**payload.model_dump())
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return device


@router.get("", response_model=list[DeviceOut])
async def list_devices(session: AsyncSession = Depends(get_session)) -> list[Device]:
    result = await session.execute(select(Device).order_by(Device.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{device_id}/manuals", response_model=list[ManualOut])
async def list_device_manuals(
    device_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> list[Manual]:
    device = await session.get(Device, device_id)
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "device not found")
    result = await session.execute(
        select(Manual).where(Manual.device_id == device_id).order_by(Manual.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/identify", response_model=IdentifyResponse)
async def identify_device(
    file: UploadFile = File(...),
    provider: LLMProviderName | None = Form(default=None),
    model: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> IdentifyResponse:
    settings = get_settings()
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"expected an image, got {file.content_type!r}",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty image")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "image too large")

    try:
        llm = get_llm_provider(settings, provider, model)
    except LLMNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    try:
        ident = await llm.identify_device(data, file.content_type)
    except NotImplementedError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface upstream vision errors
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"vision failed: {exc}") from exc

    terms = [ident.brand, ident.device_type, ident.category, *ident.keywords]
    matches = await _match_devices(session, [t for t in terms if t])

    return IdentifyResponse(
        identification=IdentificationOut(
            brand=ident.brand,
            model_number=ident.model_number,
            category=ident.category,
            device_type=ident.device_type,
            keywords=ident.keywords,
        ),
        matches=matches,
    )
