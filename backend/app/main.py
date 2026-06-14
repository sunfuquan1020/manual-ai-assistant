"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings, validate_startup
from .routers import chat, devices, manuals, providers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast if the default providers are misconfigured.
    validate_startup(get_settings())
    yield


app = FastAPI(title="说明书 AI 助手 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router)
app.include_router(manuals.router)
app.include_router(providers.router)
app.include_router(chat.router)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
