import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from bson.objectid import ObjectId

from app.main import app

# Mock data for testing
MOCK_CATEGORY_ID = str(ObjectId())
MOCK_NOTE_ID = str(ObjectId())

class TestNotesMongoDBAPI:
    """Integration tests for the Notes API with MongoDB"""
    
    @pytest.fixture
    def client(self):
        """Test client with MongoDB mocks"""
        # Create test client
        with TestClient(app) as client:
            yield client

    @patch('app.services.notes_mongodb.note_repository')
    def test_create_note(self, mock_repo, client):
        """Test note creation API with MongoDB"""
        # Mock create_note
        mock_repo.create_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Test Note",
            "content": "This is a test note",
            "category_ids": [MOCK_CATEGORY_ID],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Create a note with a category
        response = client.post(
            "/api/notes/",
            json={
                "title": "Test Note",
                "content": "This is a test note",
                "category_ids": [MOCK_CATEGORY_ID]
            }
        )
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Note"
        assert data["content"] == "This is a test note"
        assert data["category_ids"] == [MOCK_CATEGORY_ID]
        
        # Verify repository method was called
        mock_repo.create_note.assert_called_once()

    @patch('app.services.notes_mongodb.note_repository')
    def test_get_note(self, mock_repo, client):
        """Test getting a single note with MongoDB"""
        # Mock get_note
        mock_repo.get_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Test Note",
            "content": "This is a test note",
            "category_ids": [MOCK_CATEGORY_ID],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Get the note
        response = client.get(f"/api/notes/{MOCK_NOTE_ID}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == MOCK_NOTE_ID
        assert data["title"] == "Test Note"
        assert data["content"] == "This is a test note"
        
        # Verify repository method was called
        mock_repo.get_note.assert_called_once_with(MOCK_NOTE_ID)

    @patch('app.services.notes_mongodb.note_repository')
    def test_get_note_not_found(self, mock_repo, client):
        """Test getting a note that doesn't exist"""
        # Mock get_note to return None
        mock_repo.get_note.return_value = None
        
        # Get a non-existent note
        response = client.get(f"/api/notes/{MOCK_NOTE_ID}")
        
        # Verify response
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()

    @patch('app.services.notes_mongodb.note_repository')
    def test_update_note(self, mock_repo, client):
        """Test note update API with MongoDB"""
        # Mock get_note
        mock_repo.get_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Test Note",
            "content": "This is a test note",
            "category_ids": [MOCK_CATEGORY_ID],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock update_note
        mock_repo.update_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Updated Title",
            "content": "Updated content",
            "category_ids": [MOCK_CATEGORY_ID],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
        
        # Update the note
        response = client.put(
            f"/api/notes/{MOCK_NOTE_ID}",
            json={"title": "Updated Title", "content": "Updated content"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"
        
        # Verify repository method was called
        mock_repo.update_note.assert_called_once()

    @patch('app.services.notes_mongodb.note_repository')
    def test_delete_note(self, mock_repo, client):
        """Test note deletion API with MongoDB"""
        # Mock get_note
        mock_repo.get_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Test Note",
            "content": "This is a test note",
            "category_ids": [MOCK_CATEGORY_ID],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock delete_note
        mock_repo.delete_note.return_value = True
        
        # Delete the note
        response = client.delete(f"/api/notes/{MOCK_NOTE_ID}")
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify repository method was called
        mock_repo.delete_note.assert_called_once_with(MOCK_NOTE_ID)

    @patch('app.services.notes_mongodb.note_repository')
    def test_delete_note_not_found(self, mock_repo, client):
        """Test deleting a note that doesn't exist"""
        # Mock get_note to return None
        mock_repo.get_note.return_value = None
        
        # Delete a non-existent note
        response = client.delete(f"/api/notes/{MOCK_NOTE_ID}")
        
        # Verify response
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()

    @patch('app.services.notes_mongodb.note_repository')
    def test_search_notes(self, mock_repo, client):
        """Test note search API with MongoDB"""
        # Mock search_notes
        mock_notes = [
            {
                "id": str(ObjectId()),
                "title": "Python Programming",
                "content": "A note about Python programming",
                "category_ids": [],
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "id": str(ObjectId()),
                "title": "Python Tips",
                "content": "Advanced Python tips",
                "category_ids": [],
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00"
            }
        ]
        mock_repo.search_notes.return_value = mock_notes
        
        # Search for Python notes
        response = client.post(
            "/api/notes/search",
            json={"keyword": "Python"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Python" in note["title"] for note in data)
        
        # Verify repository method was called
        mock_repo.search_notes.assert_called_once()
        assert mock_repo.search_notes.call_args[1]["keyword"] == "Python"

    @patch('app.services.notes_mongodb.note_repository')
    @patch('app.services.notes_mongodb.note_analysis_service')
    def test_summarize_note(self, mock_analysis, mock_repo, client):
        """Test note summarization API"""
        # Mock get_note
        mock_repo.get_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Test Note",
            "content": "This is a test note with enough content to be summarized",
            "category_ids": [],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock generate_openai_summary
        mock_analysis.generate_openai_summary.return_value = {
            "summary": "A test note summary",
            "success": True,
            "error": None,
            "model_used": "gpt-4o"
        }
        
        # Call summarize endpoint
        response = client.get(f"/api/notes/{MOCK_NOTE_ID}/summarize")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "A test note summary"
        assert data["success"] is True
        assert data["model_used"] == "gpt-4o"
        
        # Verify repository and service methods were called
        mock_repo.get_note.assert_called_once_with(MOCK_NOTE_ID)
        mock_analysis.generate_openai_summary.assert_called_once()

    @patch('app.services.notes_mongodb.note_repository')
    @patch('app.services.notes_mongodb.note_analysis_service')
    def test_analyze_sentiment(self, mock_analysis, mock_repo, client):
        """Test note sentiment analysis API"""
        # Mock get_note
        mock_repo.get_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Test Note",
            "content": "This is a positive test note",
            "category_ids": [],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock analyze_sentiment
        mock_analysis.analyze_sentiment.return_value = "Positive"
        
        # Call sentiment endpoint
        response = client.get(f"/api/notes/{MOCK_NOTE_ID}/sentiment")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "Positive"
        assert data["note_id"] == MOCK_NOTE_ID
        
        # Verify repository and service methods were called
        mock_repo.get_note.assert_called_once_with(MOCK_NOTE_ID)
        mock_analysis.analyze_sentiment.assert_called_once()

    @patch('app.services.notes_mongodb.note_repository')
    @patch('app.services.notes_mongodb.category_repository')
    @patch('app.services.notes_mongodb.categorization_service')
    def test_suggest_category(self, mock_categorization, mock_cat_repo, mock_note_repo, client):
        """Test category suggestion API"""
        # Mock get_note
        mock_note_repo.get_note.return_value = {
            "id": MOCK_NOTE_ID,
            "title": "Work Meeting",
            "content": "Notes from the work meeting",
            "category_ids": [],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Mock get_categories
        mock_cat_repo.get_categories.return_value = [
            {
                "id": MOCK_CATEGORY_ID,
                "name": "Work",
                "description": "Work-related notes",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
        
        # Mock suggest_category
        mock_categorization.suggest_category.return_value = {
            "category": "Work",
            "confidence": 0.9,
            "keywords": ["meeting", "work", "notes"],
            "method": "openai"
        }
        
        # Call suggest-category endpoint
        response = client.post(f"/api/notes/{MOCK_NOTE_ID}/suggest-category")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Work"
        assert data["confidence"] == 0.9
        assert "meeting" in data["keywords"]
        
        # Verify repository and service methods were called
        mock_note_repo.get_note.assert_called_once_with(MOCK_NOTE_ID)
        mock_cat_repo.get_categories.assert_called_once()
        mock_categorization.suggest_category.assert_called_once()