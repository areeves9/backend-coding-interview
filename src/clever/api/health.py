"""
Health check endpoints.

This module provides endpoints for monitoring application health.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get(
    "/",
    summary="Health Check",
    description="Check if the API is running and healthy",
    response_description="API health status",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "message": "Clever Photos API is running",
        }
    )
