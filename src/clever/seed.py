"""
Seed the database with photos from photos.csv.

Usage:
    python -m clever.seed [--csv PATH] [--user-id ID]

Options:
    --csv       Path to CSV file (default: photos.csv in project root)
    --user-id   User ID to assign as owner (default: creates 'seed@clever.com' user)
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from clever.config import settings
from clever.database import AsyncSessionLocal, engine, Base
from clever.logging import configure_logging, get_logger
from clever.models import Photo, User

configure_logging(settings)
logger = get_logger(__name__)

# CSV column to model field mapping
CSV_TO_MODEL = {
    "id": "pexels_id",
    "width": "width",
    "height": "height",
    "url": "url",
    "photographer": "photographer",
    "photographer_url": "photographer_url",
    "photographer_id": "photographer_id",
    "avg_color": "avg_color",
    "src.original": "src_original",
    "src.large2x": "src_large2x",
    "src.large": "src_large",
    "src.medium": "src_medium",
    "src.small": "src_small",
    "src.portrait": "src_portrait",
    "src.landscape": "src_landscape",
    "src.tiny": "src_tiny",
    "alt": "alt",
}

SEED_USER_ID = "seed-user-00000000-0000-0000-0000-000000000000"
SEED_USER_EMAIL = "seed@clever.com"


async def get_or_create_seed_user(session, user_id: str | None = None) -> str:
    """Get or create the seed user, return user ID."""
    if user_id:
        # Verify user exists
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            logger.error(f"User {user_id} not found")
            sys.exit(1)
        return user_id

    # Create or get seed user
    result = await session.execute(select(User).where(User.id == SEED_USER_ID))
    user = result.scalar_one_or_none()

    if not user:
        user = User(id=SEED_USER_ID, email=SEED_USER_EMAIL)
        session.add(user)
        await session.commit()
        logger.info(f"Created seed user: {SEED_USER_EMAIL}")

    return SEED_USER_ID


def parse_csv_row(row: dict) -> dict:
    """Convert CSV row to Photo model fields."""
    data = {}
    for csv_col, model_field in CSV_TO_MODEL.items():
        value = row.get(csv_col, "")

        # Type conversions
        if model_field in ("pexels_id", "width", "height", "photographer_id"):
            value = int(value) if value else 0
        elif model_field == "alt":
            value = value if value else None

        data[model_field] = value

    return data


async def seed_photos(csv_path: Path, user_id: str | None = None) -> None:
    """Seed photos from CSV file."""
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        owner_id = await get_or_create_seed_user(session, user_id)

        # Read CSV
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        logger.info(f"Found {len(rows)} photos in CSV")

        # Insert photos (skip duplicates)
        inserted = 0
        skipped = 0

        for row in rows:
            photo_data = parse_csv_row(row)
            photo_data["user_id"] = owner_id

            # Check if already exists
            result = await session.execute(
                select(Photo).where(Photo.pexels_id == photo_data["pexels_id"])
            )
            if result.scalar_one_or_none():
                skipped += 1
                continue

            photo = Photo(**photo_data)
            session.add(photo)
            inserted += 1

        await session.commit()
        logger.info(f"Seeded {inserted} photos, skipped {skipped} duplicates")


def main():
    parser = argparse.ArgumentParser(description="Seed database with photos from CSV")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).parent.parent.parent / "photos.csv",
        help="Path to CSV file",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="User ID to assign as owner",
    )
    args = parser.parse_args()

    asyncio.run(seed_photos(args.csv, args.user_id))


if __name__ == "__main__":
    main()
