"""InsightIQ FastAPI application."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.version)
    # Local dev origins plus any extra origins passed via CORS_ALLOW_ORIGINS
    # (comma-separated). The regex allows any Vercel deployment (preview + prod)
    # to call the API without hardcoding the exact domain.
    default_origins = ["http://localhost:3000", "http://localhost:8501"]
    extra_origins = [
        o.strip()
        for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins + extra_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
