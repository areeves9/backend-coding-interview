"""
Supabase Auth dependencies and utilities.

This module handles JWT validation against Supabase's JWKS endpoint
and provides the get_current_user dependency for FastAPI.
"""

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession
from sqlalchemy.future import select

from clever.config import settings
from clever.database import AsyncSession, AsyncSessionLocal, get_db
from clever.models import User

# OAuth2 scheme for Bearer token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@lru_cache(maxsize=1)
async def get_jwks() -> Dict[str, Any]:
    """Fetch and cache Supabase JWKS (JSON Web Key Set)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.supabase_jwks_url)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch JWKS: {str(e)}",
        ) from e


async def validate_jwt(token: str) -> Dict[str, Any]:
    """Validate JWT token against Supabase JWKS."""
    try:
        # Get JWKS
        jwks = await get_jwks()

        # Validate token
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience="authenticated",
            options={
                "verify_aud": False
            },  # Supabase doesn't always set standard aud claim
        )

        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_or_create_user(
    db: SQLAlchemyAsyncSession, user_id: str, jwt_payload: Dict[str, Any]
) -> User:
    """Get existing user or create new user from JWT payload."""
    # Try to find existing user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        return user

    # Create new user if not found
    email = jwt_payload.get("email") or f"user_{user_id}@example.com"

    new_user = User(
        id=user_id,
        email=email,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    try:
        # Validate JWT and get payload
        payload = await validate_jwt(token)

        # Extract user ID from sub claim
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID",
            )

        # Get or create user in database
        user = await get_or_create_user(db, user_id, payload)

        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        ) from e
