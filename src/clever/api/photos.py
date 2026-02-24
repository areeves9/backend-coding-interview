"""
Photo API endpoints.

This module provides CRUD endpoints for managing photos.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select as sql_select
from sqlalchemy.ext.asyncio import AsyncSession

from clever.auth.deps import get_current_user
from clever.database import get_db
from clever.models import Photo, User
from clever.schemas import (PaginationBase, PhotoCreate, PhotoListResponse,
                            PhotoResponse, PhotoUpdate)

router = APIRouter(
    tags=["photos"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    summary="List Photos",
    description="List all photos with pagination and filtering",
    response_model=PhotoListResponse,
    response_description="Paginated list of photos",
)
async def list_photos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    photographer_id: Optional[int] = Query(
        None, description="Filter by photographer ID"
    ),
) -> PhotoListResponse:
    """List photos with pagination and optional filtering."""
    # Build query
    query = sql_select(Photo)

    # Apply filters
    if photographer_id:
        query = query.where(Photo.photographer_id == photographer_id)

    # Count total items
    count_query = sql_select(func.count()).select_from(Photo)
    if photographer_id:
        count_query = count_query.where(Photo.photographer_id == photographer_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    photos = result.scalars().all()

    # Calculate pagination info
    pages = (total + limit - 1) // limit if limit > 0 else 0

    return PhotoListResponse(
        items=[PhotoResponse.model_validate(photo) for photo in photos],
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get(
    "/{photo_id}",
    summary="Get Photo",
    description="Get a single photo by ID",
    response_model=PhotoResponse,
    response_description="Photo details",
)
async def get_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    """Get a single photo by ID."""
    # Find photo
    result = await db.execute(sql_select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    return PhotoResponse.model_validate(photo)


@router.post(
    "/",
    summary="Create Photo",
    description="Create a new photo",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Created photo details",
)
async def create_photo(
    photo_data: PhotoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    """Create a new photo."""
    # Check if photo with same pexels_id already exists
    existing = await db.execute(
        sql_select(Photo).where(Photo.pexels_id == photo_data.pexels_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Photo with this Pexels ID already exists",
        )

    # Create new photo
    new_photo = Photo(**photo_data.model_dump(), user_id=current_user.id)

    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)

    return PhotoResponse.model_validate(new_photo)


@router.put(
    "/{photo_id}",
    summary="Update Photo",
    description="Fully update a photo (requires ownership)",
    response_model=PhotoResponse,
    response_description="Updated photo details",
)
async def update_photo(
    photo_id: int,
    photo_data: PhotoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    """Fully update a photo."""
    # Find photo
    result = await db.execute(sql_select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    # Check ownership
    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own photos",
        )

    # Update photo
    for key, value in photo_data.model_dump().items():
        setattr(photo, key, value)

    await db.commit()
    await db.refresh(photo)

    return PhotoResponse.model_validate(photo)


@router.patch(
    "/{photo_id}",
    summary="Partial Update Photo",
    description="Partially update a photo (requires ownership)",
    response_model=PhotoResponse,
    response_description="Updated photo details",
)
async def partial_update_photo(
    photo_id: int,
    photo_data: PhotoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    """Partially update a photo."""
    # Find photo
    result = await db.execute(sql_select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    # Check ownership
    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own photos",
        )

    # Update only provided fields
    for key, value in photo_data.model_dump(exclude_unset=True).items():
        setattr(photo, key, value)

    await db.commit()
    await db.refresh(photo)

    return PhotoResponse.model_validate(photo)


@router.delete(
    "/{photo_id}",
    summary="Delete Photo",
    description="Delete a photo (requires ownership)",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Photo deleted successfully",
)
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a photo."""
    # Find photo
    result = await db.execute(sql_select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    # Check ownership
    if photo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own photos",
        )

    # Delete photo
    await db.delete(photo)
    await db.commit()