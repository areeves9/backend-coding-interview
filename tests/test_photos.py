"""
Tests for photo API endpoints.

This module contains unit tests for the photo CRUD operations.
"""

import pytest
from httpx import AsyncClient

from clever.models import Photo, User
from tests.conftest import SAMPLE_PHOTO_DATA


class TestListPhotos:
    """Tests for GET /api/v1/photos/"""

    @pytest.mark.asyncio
    async def test_list_photos_empty(self, client: AsyncClient):
        """Test listing photos when none exist."""
        response = await client.get("/api/v1/photos/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_photos_with_data(
        self, client: AsyncClient, sample_photo: Photo
    ):
        """Test listing photos returns existing photos."""
        response = await client.get("/api/v1/photos/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["pexels_id"] == sample_photo.pexels_id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "page,limit,expected_page,expected_limit",
        [
            (1, 10, 1, 10),
            (2, 20, 2, 20),
            (5, 50, 5, 50),
            (1, 100, 1, 100),
        ],
    )
    async def test_list_photos_pagination(
        self,
        client: AsyncClient,
        page: int,
        limit: int,
        expected_page: int,
        expected_limit: int,
    ):
        """Test pagination parameters."""
        response = await client.get(f"/api/v1/photos/?page={page}&limit={limit}")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == expected_page
        assert data["limit"] == expected_limit

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "photographer_id,expected_total",
        [
            (100, 1),  # Matching photographer (sample_photo has photographer_id=100)
            (99999, 0),  # Non-matching photographer
        ],
    )
    async def test_list_photos_filter_by_photographer(
        self,
        client: AsyncClient,
        sample_photo: Photo,
        photographer_id: int,
        expected_total: int,
    ):
        """Test filtering by photographer_id."""
        response = await client.get(
            f"/api/v1/photos/?photographer_id={photographer_id}"
        )
        assert response.status_code == 200
        assert response.json()["total"] == expected_total


class TestGetPhoto:
    """Tests for GET /api/v1/photos/{photo_id}"""

    @pytest.mark.asyncio
    async def test_get_photo_success(self, client: AsyncClient, sample_photo: Photo):
        """Test getting a photo by ID."""
        response = await client.get(f"/api/v1/photos/{sample_photo.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_photo.id
        assert data["pexels_id"] == sample_photo.pexels_id
        assert data["photographer"] == sample_photo.photographer

    @pytest.mark.asyncio
    @pytest.mark.parametrize("photo_id", [99999, 0, 999999999])
    async def test_get_photo_not_found(self, client: AsyncClient, photo_id: int):
        """Test getting a non-existent photo returns 404."""
        response = await client.get(f"/api/v1/photos/{photo_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Photo not found"


class TestCreatePhoto:
    """Tests for POST /api/v1/photos/"""

    @pytest.mark.asyncio
    async def test_create_photo_success(self, client: AsyncClient, test_user: User):
        """Test creating a new photo."""
        response = await client.post("/api/v1/photos/", json=SAMPLE_PHOTO_DATA)

        assert response.status_code == 201
        data = response.json()
        assert data["pexels_id"] == SAMPLE_PHOTO_DATA["pexels_id"]
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_photo_duplicate_pexels_id(
        self, client: AsyncClient, sample_photo: Photo
    ):
        """Test creating a photo with duplicate pexels_id returns 409."""
        duplicate_data = SAMPLE_PHOTO_DATA.copy()
        duplicate_data["pexels_id"] = sample_photo.pexels_id

        response = await client.post("/api/v1/photos/", json=duplicate_data)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_data,description",
        [
            ({"pexels_id": "not_a_number"}, "pexels_id should be integer"),
            ({}, "missing all required fields"),
            ({"pexels_id": 123}, "missing other required fields"),
            (
                {**SAMPLE_PHOTO_DATA, "url": "not_a_valid_url"},
                "invalid URL format",
            ),
        ],
    )
    async def test_create_photo_invalid_data(
        self, client: AsyncClient, invalid_data: dict, description: str
    ):
        """Test creating a photo with invalid data returns 422."""
        response = await client.post("/api/v1/photos/", json=invalid_data)

        assert response.status_code == 422, f"Failed for: {description}"


class TestUpdatePhoto:
    """Tests for PUT /api/v1/photos/{photo_id}"""

    @pytest.mark.asyncio
    async def test_update_photo_success(self, client: AsyncClient, sample_photo: Photo):
        """Test fully updating a photo."""
        update_data = SAMPLE_PHOTO_DATA.copy()
        update_data["alt"] = "Updated description"

        response = await client.put(
            f"/api/v1/photos/{sample_photo.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["alt"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_photo_not_found(self, client: AsyncClient):
        """Test updating a non-existent photo returns 404."""
        response = await client.put("/api/v1/photos/99999", json=SAMPLE_PHOTO_DATA)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_photo_not_owner(
        self,
        client: AsyncClient,
        other_user_photo: Photo,
    ):
        """Test updating another user's photo returns 403."""
        response = await client.put(
            f"/api/v1/photos/{other_user_photo.id}", json=SAMPLE_PHOTO_DATA
        )

        assert response.status_code == 403
        assert "only update your own" in response.json()["detail"]


class TestPartialUpdatePhoto:
    """Tests for PATCH /api/v1/photos/{photo_id}"""

    @pytest.mark.asyncio
    async def test_partial_update_success(
        self, client: AsyncClient, sample_photo: Photo
    ):
        """Test partially updating a photo."""
        response = await client.patch(
            f"/api/v1/photos/{sample_photo.id}",
            json={"alt": "Partially updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["alt"] == "Partially updated"
        # Other fields unchanged
        assert data["width"] == sample_photo.width

    @pytest.mark.asyncio
    async def test_partial_update_not_found(self, client: AsyncClient):
        """Test partial update of non-existent photo returns 404."""
        response = await client.patch("/api/v1/photos/99999", json={"alt": "Updated"})

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_partial_update_not_owner(
        self,
        client: AsyncClient,
        other_user_photo: Photo,
    ):
        """Test partial update of another user's photo returns 403."""
        response = await client.patch(
            f"/api/v1/photos/{other_user_photo.id}",
            json={"alt": "Trying to update"},
        )

        assert response.status_code == 403


class TestDeletePhoto:
    """Tests for DELETE /api/v1/photos/{photo_id}"""

    @pytest.mark.asyncio
    async def test_delete_photo_success(self, client: AsyncClient, sample_photo: Photo):
        """Test deleting a photo."""
        response = await client.delete(f"/api/v1/photos/{sample_photo.id}")

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/api/v1/photos/{sample_photo.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_photo_not_found(self, client: AsyncClient):
        """Test deleting a non-existent photo returns 404."""
        response = await client.delete("/api/v1/photos/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_photo_not_owner(
        self,
        client: AsyncClient,
        other_user_photo: Photo,
    ):
        """Test deleting another user's photo returns 403."""
        response = await client.delete(f"/api/v1/photos/{other_user_photo.id}")

        assert response.status_code == 403
        assert "only delete your own" in response.json()["detail"]
