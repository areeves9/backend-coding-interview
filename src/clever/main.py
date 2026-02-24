"""
FastAPI application factory for Clever Photos API.

This module creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clever.api.router import api_router
from clever.config import settings
from clever.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Clean up resources if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Clever Photos API",
        description="Photo management service for Clever Real Estate assessment",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include API routers
    app.include_router(api_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_app()
