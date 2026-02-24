"""
SQLAlchemy models for the application.

This module defines the database models using SQLAlchemy 2.0 declarative base.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from clever.database import Base


class User(Base):
    """User model representing authenticated users from Supabase Auth."""

    __tablename__ = "users"

    # User ID from Supabase Auth (UUID string)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # User email
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to photos (one-to-many)
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.id} ({self.email})>"


class Photo(Base):
    """Photo model representing images from the Pexels dataset."""

    __tablename__ = "photos"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Pexels photo ID (unique identifier from source)
    pexels_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )

    # Image dimensions
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    # URLs
    url: Mapped[str] = mapped_column(Text, nullable=False)
    photographer_url: Mapped[str] = mapped_column(Text, nullable=False)
    src_original: Mapped[str] = mapped_column(Text, nullable=False)
    src_large2x: Mapped[str] = mapped_column(Text, nullable=False)
    src_large: Mapped[str] = mapped_column(Text, nullable=False)
    src_medium: Mapped[str] = mapped_column(Text, nullable=False)
    src_small: Mapped[str] = mapped_column(Text, nullable=False)
    src_portrait: Mapped[str] = mapped_column(Text, nullable=False)
    src_landscape: Mapped[str] = mapped_column(Text, nullable=False)
    src_tiny: Mapped[str] = mapped_column(Text, nullable=False)

    # Photographer information
    photographer: Mapped[str] = mapped_column(Text, nullable=False)
    photographer_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    # Color and description
    avg_color: Mapped[str] = mapped_column(String(10), nullable=False)
    alt: Mapped[str] = mapped_column(Text, nullable=True)

    # Ownership
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to user (many-to-one)
    user: Mapped["User"] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        return f"<Photo {self.pexels_id} by {self.photographer}>"


# Indexes for performance
# These will be created automatically by SQLAlchemy based on the column definitions above
