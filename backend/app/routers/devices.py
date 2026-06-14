"""Device endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Device, Manual
from ..schemas import DeviceCreate, DeviceOut, ManualOut

router = APIRouter(prefix="/devices", tags=["devices"])


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
