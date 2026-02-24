"""
Pydantic schemas for request/response validation.

This module defines data models for API input/output validation.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, constr


# ========== Photo Schemas ==========
class PhotoBase(BaseModel):
    """Base photo schema with common fields."""

    pexels_id: int = Field(..., description="Unique Pexels photo ID")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    url: HttpUrl = Field(..., description="Pexels photo URL")
    photographer: str = Field(..., description="Photographer name")
    photographer_url: HttpUrl = Field(..., description="Photographer profile URL")
    photographer_id: int = Field(..., description="Photographer ID")
    avg_color: constr(pattern=r"^#[0-9A-Fa-f]{6}$") = Field(
        ..., description="Average color hex code"
    )
    src_original: HttpUrl = Field(..., description="Original image URL")
    src_large2x: HttpUrl = Field(..., description="Large 2x image URL")
    src_large: HttpUrl = Field(..., description="Large image URL")
    src_medium: HttpUrl = Field(..., description="Medium image URL")
    src_small: HttpUrl = Field(..., description="Small image URL")
    src_portrait: HttpUrl = Field(..., description="Portrait image URL")
    src_landscape: HttpUrl = Field(..., description="Landscape image URL")
    src_tiny: HttpUrl = Field(..., description="Tiny image URL")
    alt: Optional[str] = Field(None, description="Alternative text/description")


class PhotoCreate(PhotoBase):
    """Schema for creating new photos."""

    pass


class PhotoUpdate(BaseModel):
    """Schema for updating photos (partial updates)."""

    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")
    alt: Optional[str] = Field(None, description="Alternative text/description")


class PhotoResponse(PhotoBase):
    """Schema for photo responses including metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Database ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ========== User Schemas ==========
class UserBase(BaseModel):
    """Base user schema."""

    email: str = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for creating users."""

    password: str = Field(..., min_length=8, description="User password")


class UserResponse(UserBase):
    """Schema for user responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")


# ========== Pagination Schema ==========
class PaginationBase(BaseModel):
    """Base pagination schema."""

    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class PhotoListResponse(BaseModel):
    """Schema for paginated photo lists."""

    items: List[PhotoResponse] = Field(..., description="List of photos")
    total: int = Field(..., description="Total number of photos")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


# ========== Error Schemas ==========
class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(..., description="Error message")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""

    detail: List[dict] = Field(..., description="Validation error details")
