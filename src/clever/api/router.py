"""
Main API router.

This module combines all API endpoints into a single router.
"""

from fastapi import APIRouter

from clever.api.health import router as health_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, prefix="/health", tags=["health"])

# Note: Other routers (photos, auth) will be added here as they are implemented
# api_router.include_router(photos_router, prefix="/photos", tags=["photos"])
# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
