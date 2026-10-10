"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from paa import __version__
from paa.api.routes import area, comparables, listings, meta, postcodes
from paa.config import get_settings
from paa.db import make_pool


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = make_pool()
    pool.open()
    app.state.pool = pool
    try:
        yield
    finally:
        pool.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Property Acquisition Analyser API",
        version=__version__,
        lifespan=_lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(meta.router, prefix="/api")
    app.include_router(postcodes.router, prefix="/api")
    app.include_router(area.router, prefix="/api")
    app.include_router(comparables.router, prefix="/api")
    app.include_router(listings.router, prefix="/api")
    return app
