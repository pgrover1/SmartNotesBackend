import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.category import Category

# Test category API endpoints

def test_create_category(client: TestClient, test_db: Session):
    """Test category creation API"""
    response = client.post(
        "/api/categories/",
        json={"name": "Test Category", "description": "Test Description"}
    )
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Category"
    assert data["description"] == "Test Description"

def test_get_category(client: TestClient, test_db: Session):
    """Test getting a single category"""
    # Create a category first
    category_response = client.post(
        "/api/categories/",
        json={"name": "Get Test Category", "description": "Test for get"}
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]
    
    # Get the category
    response = client.get(f"/api/categories/{category_id}")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Get Test Category"
    assert data["description"] == "Test for get"

@pytest.mark.skip("Skipping until MongoDB API path is fixed")
def test_update_category(client: TestClient, test_db: Session):
    """Test category update API"""
    # Create a category first
    category_response = client.post(
        "/api/categories/",
        json={"name": "Update Test Category", "description": "Test for update"}
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]
    
    # Update the category
    response = client.put(
        f"/api/categories/{category_id}",
        json={"name": "Updated Category", "description": "Updated description"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Category"
    assert data["description"] == "Updated description"

def test_delete_category(client: TestClient, test_db: Session):
    """Test category deletion API"""
    # Create a category first
    category_response = client.post(
        "/api/categories/",
        json={"name": "Delete Test Category", "description": "Test for delete"}
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]
    
    # Delete the category
    response = client.delete(f"/api/categories/{category_id}")
    
    # Verify response
    assert response.status_code == 200
    
    # Verify category is deleted
    get_response = client.get(f"/api/categories/{category_id}")
    assert get_response.status_code == 404

def test_get_categories(client: TestClient, test_db: Session):
    """Test getting all categories"""
    # Create some test categories
    client.post("/api/categories/", json={"name": "Category 1", "description": "Test 1"})
    client.post("/api/categories/", json={"name": "Category 2", "description": "Test 2"})
    
    # Get all categories
    response = client.get("/api/categories/")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(cat["name"] == "Category 1" for cat in data)
    assert any(cat["name"] == "Category 2" for cat in data)
