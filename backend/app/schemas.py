"""Pydantic request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .config import LLMProviderName
from .models import ManualStatus


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    brand: str | None = None
    model_number: str | None = None
    category: str | None = None


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    brand: str | None
    model_number: str | None
    category: str | None
    created_at: datetime


class ManualOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_id: uuid.UUID | None
    filename: str
    content_type: str
    size_bytes: int
    status: ManualStatus
    embedding_model: str | None
    page_count: int | None
    error: str | None
    created_at: datetime


# ---- Chat ----

class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    device_id: uuid.UUID | None = None
    manual_id: uuid.UUID | None = None
    messages: list[ChatMessage] = Field(min_length=1)
    provider: LLMProviderName | None = None
    model: str | None = None


class SourceOut(BaseModel):
    chunk_id: uuid.UUID
    manual_id: uuid.UUID
    page: int
    snippet: str


# ---- Providers ----

class ProviderModelInfo(BaseModel):
    provider: str
    available: bool
    default_model: str
    models: list[str]
