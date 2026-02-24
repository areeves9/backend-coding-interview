"""
Supabase Auth dependencies and utilities.

This module handles JWT validation using Supabase's JWKS endpoint
and provides the get_current_user dependency for FastAPI.
"""

from typing import Any, Dict

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession
from sqlalchemy.future import select

from clever.config import settings
from clever.database import AsyncSession, get_db
from clever.models import User

# OAuth2 scheme for Bearer token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Cache for JWKS
_jwks_cache: Dict[str, Any] | None = None


async def get_jwks() -> Dict[str, Any]:
    """Fetch and cache Supabase JWKS (JSON Web Key Set)."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.supabase_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            return _jwks_cache
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch JWKS: {str(e)}",
        ) from e


async def validate_jwt(token: str) -> Dict[str, Any]:
    """Validate JWT token using Supabase JWKS."""
    try:
        # Get JWKS
        jwks_data = await get_jwks()

        # Get the key ID from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Find the matching key
        rsa_key = None
        for key in jwks_data.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find matching key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode and validate token (Supabase uses ES256)
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["ES256"],
            audience="authenticated",
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
