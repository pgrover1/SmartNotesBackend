import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.note import Note
from app.models.category import Category

# Test note API endpoints

def test_create_note(client: TestClient, test_db: Session):
    """Test note creation API"""
    # Create a test category first
    category_response = client.post(
        "/api/categories/",
        json={"name": "Test Category", "description": "Test Description"}
    )
    assert category_response.status_code == 201
    category_id = category_response.json()["id"]
    
    # Create a note with the category
    response = client.post(
        "/api/notes/",
        json={
            "title": "Test Note",
            "content": "This is a test note",
            "category_ids": [category_id]
        }
    )
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["content"] == "This is a test note"
    assert len(data["categories"]) == 1
    assert data["categories"][0]["id"] == category_id

def test_get_note(client: TestClient, test_db: Session):
    """Test getting a single note"""
    # Create a note first
    note_response = client.post(
        "/api/notes/",
        json={"title": "Get Test Note", "content": "This is a test note for get"}
    )
    assert note_response.status_code == 201
    note_id = note_response.json()["id"]
    
    # Get the note
    response = client.get(f"/api/notes/{note_id}")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Get Test Note"
    assert data["content"] == "This is a test note for get"

def test_update_note(client: TestClient, test_db: Session):
    """Test note update API"""
    # Create a note first
    note_response = client.post(
        "/api/notes/",
        json={"title": "Update Test Note", "content": "This is a test note for update"}
    )
    assert note_response.status_code == 201
    note_id = note_response.json()["id"]
    
    # Update the note
    response = client.put(
        f"/api/notes/{note_id}",
        json={"title": "Updated Title", "content": "Updated content"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Updated content"

def test_delete_note(client: TestClient, test_db: Session):
    """Test note deletion API"""
    # Create a note first
    note_response = client.post(
        "/api/notes/",
        json={"title": "Delete Test Note", "content": "This is a test note for delete"}
    )
    assert note_response.status_code == 201
    note_id = note_response.json()["id"]
    
    # Delete the note
    response = client.delete(f"/api/notes/{note_id}")
    
    # Verify response
    assert response.status_code == 200
    
    # Verify note is deleted
    get_response = client.get(f"/api/notes/{note_id}")
    assert get_response.status_code == 404

def test_search_notes(client: TestClient, test_db: Session):
    """Test note search API"""
    # Create some test notes
    client.post(
        "/api/notes/",
        json={"title": "Python Programming", "content": "A note about Python programming"}
    )
    client.post(
        "/api/notes/",
        json={"title": "JavaScript Basics", "content": "Learning JavaScript fundamentals"}
    )
    
    # Search for Python notes
    response = client.post(
        "/api/notes/search",
        json={"keyword": "Python"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any("Python" in note["title"] for note in data)
