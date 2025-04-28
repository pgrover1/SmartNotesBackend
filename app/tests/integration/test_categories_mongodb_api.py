import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from bson.objectid import ObjectId

from app.main import app

# Mock data for testing
MOCK_CATEGORY_ID = str(ObjectId())

class TestCategoriesMongoDBAPI:
    """Integration tests for the Categories API with MongoDB"""
    
    @pytest.fixture
    def client(self):
        """Test client with MongoDB mocks"""
        # Create test client
        with TestClient(app) as client:
            yield client

    @patch('app.services.categories_mongodb.category_repository')
    def test_create_category(self, mock_repo, client):
        """Test category creation API with MongoDB"""
        # Mock create_category
        mock_repo.create_category.return_value = {
            "id": MOCK_CATEGORY_ID,
            "name": "Test Category",
            "description": "Test Description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock get_category_by_name
        mock_repo.get_category_by_name.return_value = None
        
        # Create a category
        response = client.post(
            "/api/categories/",
            json={
                "name": "Test Category",
                "description": "Test Description"
            }
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Category"
        assert data["description"] == "Test Description"
        
        # Verify repository method was called
        mock_repo.create_category.assert_called_once()

    @patch('app.services.categories_mongodb.category_repository')
    def test_create_duplicate_category(self, mock_repo, client):
        """Test creating a category with a duplicate name"""
        # Mock get_category_by_name to return an existing category
        mock_repo.get_category_by_name.return_value = {
            "id": MOCK_CATEGORY_ID,
            "name": "Test Category",
            "description": "Existing Description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Try to create a category with the same name
        response = client.post(
            "/api/categories/",
            json={
                "name": "Test Category",
                "description": "Test Description"
            }
        )
        
        # Verify response indicates existing category is returned
        assert response.status_code == 201  # Returns existing category
        data = response.json()
        assert data["id"] == MOCK_CATEGORY_ID
        assert data["description"] == "Existing Description"
        
        # Verify create_category was not called
        mock_repo.create_category.assert_not_called()

    @patch('app.services.categories_mongodb.category_repository')
    def test_get_categories(self, mock_repo, client):
        """Test getting all categories"""
        # Mock get_categories
        mock_repo.get_categories.return_value = [
            {
                "id": MOCK_CATEGORY_ID,
                "name": "Test Category",
                "description": "Test Description",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": str(ObjectId()),
                "name": "Another Category",
                "description": "Another Description",
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00"
            }
        ]
        
        # Get all categories
        response = client.get("/api/categories/")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Test Category"
        assert data[1]["name"] == "Another Category"
        
        # Verify repository method was called
        mock_repo.get_categories.assert_called_once()

    @patch('app.services.categories_mongodb.category_repository')
    def test_get_category(self, mock_repo, client):
        """Test getting a single category"""
        # Mock get_category
        mock_repo.get_category.return_value = {
            "id": MOCK_CATEGORY_ID,
            "name": "Test Category",
            "description": "Test Description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Get the category
        response = client.get(f"/api/categories/{MOCK_CATEGORY_ID}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == MOCK_CATEGORY_ID
        assert data["name"] == "Test Category"
        assert data["description"] == "Test Description"
        
        # Verify repository method was called
        mock_repo.get_category.assert_called_once_with(MOCK_CATEGORY_ID)

    @patch('app.services.categories_mongodb.category_repository')
    def test_get_category_not_found(self, mock_repo, client):
        """Test getting a category that doesn't exist"""
        # Mock get_category to return None
        mock_repo.get_category.return_value = None
        
        # Get a non-existent category
        response = client.get(f"/api/categories/{MOCK_CATEGORY_ID}")
        
        # Verify response
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()

    @patch('app.services.categories_mongodb.category_repository')
    def test_update_category(self, mock_repo, client):
        """Test category update API"""
        # Mock get_category
        mock_repo.get_category.return_value = {
            "id": MOCK_CATEGORY_ID,
            "name": "Test Category",
            "description": "Test Description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock update_category
        mock_repo.update_category.return_value = {
            "id": MOCK_CATEGORY_ID,
            "name": "Updated Category",
            "description": "Updated Description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
        
        # Update the category
        response = client.put(
            f"/api/categories/{MOCK_CATEGORY_ID}",
            json={
                "name": "Updated Category",
                "description": "Updated Description"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["description"] == "Updated Description"
        
        # Verify repository method was called
        mock_repo.update_category.assert_called_once()

    @patch('app.services.categories_mongodb.category_repository')
    def test_update_category_not_found(self, mock_repo, client):
        """Test updating a category that doesn't exist"""
        # Mock get_category to return None
        mock_repo.get_category.return_value = None
        
        # Update a non-existent category
        response = client.put(
            f"/api/categories/{MOCK_CATEGORY_ID}",
            json={
                "name": "Updated Category",
                "description": "Updated Description"
            }
        )
        
        # Verify response
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()
        
        # Verify update_category was not called
        mock_repo.update_category.assert_not_called()

    @patch('app.services.categories_mongodb.category_repository')
    def test_delete_category(self, mock_repo, client):
        """Test category deletion API"""
        # Mock get_category
        mock_repo.get_category.return_value = {
            "id": MOCK_CATEGORY_ID,
            "name": "Test Category",
            "description": "Test Description",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock delete_category
        mock_repo.delete_category.return_value = True
        
        # Delete the category
        response = client.delete(f"/api/categories/{MOCK_CATEGORY_ID}")
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify repository method was called
        mock_repo.delete_category.assert_called_once_with(MOCK_CATEGORY_ID)

    @patch('app.services.categories_mongodb.category_repository')
    def test_delete_category_not_found(self, mock_repo, client):
        """Test deleting a category that doesn't exist"""
        # Mock get_category to return None
        mock_repo.get_category.return_value = None
        
        # Delete a non-existent category
        response = client.delete(f"/api/categories/{MOCK_CATEGORY_ID}")
        
        # Verify response
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()
        
        # Verify delete_category was not called
        mock_repo.delete_category.assert_not_called()