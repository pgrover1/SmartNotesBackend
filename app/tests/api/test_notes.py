import unittest
from unittest.mock import MagicMock, AsyncMock
from typing import List, Optional, Union, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.routing import APIRouter
from fastapi.params import Depends, Query
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from bson.objectid import ObjectId
from bson.errors import InvalidId

from app.api.routes.notes import router as notes_router
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, NoteSearchQuery, NoteMongoResponse
from app.api.routes.notes import note_service
from app.api.routes.categories import category_service
from app.services.categorization import CategorizationService
from app.services.note_analysis import NoteAnalysisService
from app.db.provider import get_db  # Import for mocking purposes
from app.dependencies import enhance_note_with_categories  # Import for mocking purposes
from app.services.factory import get_note_service, get_category_service, get_categorization_service, get_note_analysis_service

class TestNotesRouter(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()
        self.note_service_mock = MagicMock(spec=note_service)
        self.category_service_mock = MagicMock(spec=category_service)
        self.categorization_service_mock = MagicMock(spec=CategorizationService)
        self.note_analysis_service_mock = MagicMock(spec=NoteAnalysisService)
        self.db_mock = MagicMock()
        self.enhance_note_mock = MagicMock()

        # For FastAPI's dependency injection, we can use synchronous functions
        def override_get_db():
            return self.db_mock

        def override_get_note_service():
            return self.note_service_mock

        def override_get_category_service():
            return self.category_service_mock

        def override_get_categorization_service():
            return self.categorization_service_mock

        def override_get_note_analysis_service():
            return self.note_analysis_service_mock

        def override_enhance_note_with_categories(note, db):
            return self.enhance_note_mock(note, db)

        self.app.dependency_overrides[get_db] = override_get_db
        self.app.dependency_overrides[get_note_service] = override_get_note_service
        self.app.dependency_overrides[get_category_service] = override_get_category_service
        self.app.dependency_overrides[get_categorization_service] = override_get_categorization_service
        self.app.dependency_overrides[get_note_analysis_service] = override_get_note_analysis_service
        self.app.dependency_overrides[enhance_note_with_categories] = override_enhance_note_with_categories

        # Include the router with the correct prefix (likely /api/notes)
        self.app.include_router(notes_router, prefix="/api/notes")
        
        # Use TestClient from FastAPI for testing
        self.client = TestClient(self.app)

    def test_get_notes(self):
        mock_notes = [{"_id": ObjectId(), "title": "Test Note 1", "content": "Content 1"}, {"_id": ObjectId(), "title": "Test Note 2", "content": "Content 2"}]
        self.note_service_mock.get_notes.return_value = mock_notes
        self.enhance_note_mock.side_effect = lambda note, db: note  # Simulate enhancement

        response = self.client.get("/api/notes/")
        self.assertEqual(response.status_code, 200)

    async def test_create_note(self):
        note_in = NoteCreate(title="New Note", content="New Content")
        mock_created_note = {"_id": ObjectId(), "title": "New Note", "content": "New Content"}
        self.note_service_mock.create_note.return_value = mock_created_note
        self.enhance_note_mock.return_value = mock_created_note

        response = await self.client.post("/notes/", json=note_in.model_dump())
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(response.json()["title"], "New Note")
        self.note_service_mock.create_note.assert_called_once_with(self.db_mock, note_in=note_in)
        self.enhance_note_mock.assert_called_once_with(mock_created_note, self.db_mock)

    async def test_get_note_valid_id(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Existing Note", "content": "Existing Content"}
        self.note_service_mock.get_note.return_value = mock_note
        self.enhance_note_mock.return_value = mock_note

        response = await self.client.get(f"/notes/{note_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Existing Note")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.enhance_note_mock.assert_called_once_with(mock_note, self.db_mock)

    async def test_get_note_invalid_id(self):
        response = await self.client.get("/notes/invalid_id")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid MongoDB ID format")
        self.note_service_mock.get_note.assert_not_called()
        self.enhance_note_mock.assert_not_called()

    async def test_get_note_not_found(self):
        note_id = str(ObjectId())
        self.note_service_mock.get_note.return_value = None

        response = await self.client.get(f"/notes/{note_id}")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Note not found")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.enhance_note_mock.assert_not_called()

    async def test_update_note_valid_id(self):
        note_id = str(ObjectId())
        note_in = NoteUpdate(title="Updated Note")
        mock_updated_note = {"_id": ObjectId(note_id), "title": "Updated Note", "content": "Existing Content"}
        self.note_service_mock.update_note.return_value = mock_updated_note
        self.enhance_note_mock.return_value = mock_updated_note

        # Use synchronous client request
        response = self.client.put(f"/notes/{note_id}", json=note_in.dict(exclude_unset=True))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated Note")
        self.note_service_mock.update_note.assert_called_once_with(self.db_mock, note_id=note_id, note_in=note_in)
        self.enhance_note_mock.assert_called_once_with(mock_updated_note, self.db_mock)

    async def test_update_note_invalid_id(self):
        note_in = NoteUpdate(title="Updated Note")
        response = await self.client.put("/notes/invalid_id", json=note_in.model_dump(exclude_unset=True))
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid MongoDB ID format")
        self.note_service_mock.update_note.assert_not_called()
        self.enhance_note_mock.assert_not_called()

    async def test_update_note_not_found(self):
        note_id = str(ObjectId())
        note_in = NoteUpdate(title="Updated Note")
        self.note_service_mock.update_note.return_value = None

        response = await self.client.put(f"/notes/{note_id}", json=note_in.model_dump(exclude_unset=True))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Note not found")
        self.note_service_mock.update_note.assert_called_once_with(self.db_mock, note_id=note_id, note_in=note_in)
        self.enhance_note_mock.assert_not_called()

    async def test_delete_note_valid_id(self):
        note_id = str(ObjectId())
        mock_deleted_note = {"_id": ObjectId(note_id), "title": "Deleted Note", "content": "Existing Content"}
        self.note_service_mock.delete_note.return_value = mock_deleted_note
        self.enhance_note_mock.return_value = mock_deleted_note

        response = await self.client.delete(f"/notes/{note_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Deleted Note")
        self.note_service_mock.delete_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.enhance_note_mock.assert_called_once_with(mock_deleted_note, self.db_mock)

    async def test_delete_note_invalid_id(self):
        response = await self.client.delete("/notes/invalid_id")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid MongoDB ID format")
        self.note_service_mock.delete_note.assert_not_called()
        self.enhance_note_mock.assert_not_called()

    async def test_delete_note_not_found(self):
        note_id = str(ObjectId())
        self.note_service_mock.delete_note.return_value = None

        response = await self.client.delete(f"/notes/{note_id}")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Note not found")
        self.note_service_mock.delete_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.enhance_note_mock.assert_not_called()

    async def test_search_notes(self):
        query = NoteSearchQuery(title="Test")
        mock_results = [{"_id": ObjectId(), "title": "Test Note", "content": "Content"}]
        self.note_service_mock.search_notes.return_value = mock_results
        self.enhance_note_mock.side_effect = lambda note, db: note

        response = await self.client.post("/notes/search", json=query.model_dump())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Test Note")
        self.note_service_mock.search_notes.assert_called_once_with(self.db_mock, query=query, skip=0, limit=100)
        self.assertEqual(self.enhance_note_mock.call_count, 1)

    async def test_suggest_category_for_note_valid_id(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Science Article", "content": "Details about physics."}
        self.note_service_mock.get_note.return_value = mock_note
        self.categorization_service_mock.suggest_category.return_value = {"category": "Science"}

        response = await self.client.post(f"/notes/{note_id}/suggest-category")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"category": "Science"})
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.categorization_service_mock.suggest_category.assert_called_once_with("Science Article", "Details about physics.")

    async def test_suggest_category_for_note_invalid_id(self):
        response = await self.client.post("/notes/invalid_id/suggest-category")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid MongoDB ID format")
        self.note_service_mock.get_note.assert_not_called()
        self.categorization_service_mock.suggest_category.assert_not_called()

    async def test_suggest_category_for_note_not_found(self):
        note_id = str(ObjectId())
        self.note_service_mock.get_note.return_value = None

        response = await self.client.post(f"/notes/{note_id}/suggest-category")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Note not found")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.categorization_service_mock.suggest_category.assert_not_called()

    async def test_get_note_sentiment_valid_id_with_content(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Happy Note", "content": "This is a happy day."}
        self.note_service_mock.get_note.return_value = mock_note
        self.note_analysis_service_mock.analyze_sentiment.return_value = "Positive"

        response = await self.client.get(f"/notes/{note_id}/sentiment")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"sentiment": "Positive"})
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.analyze_sentiment.assert_called_once_with("This is a happy day.")

    async def test_get_note_sentiment_invalid_id(self):
        response = await self.client.get("/notes/invalid_id/sentiment")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid MongoDB ID format")
        self.note_service_mock.get_note.assert_not_called()
        self.note_analysis_service_mock.analyze_sentiment.assert_not_called()

    async def test_get_note_sentiment_not_found(self):
        note_id = str(ObjectId())
        self.note_service_mock.get_note.return_value = None

        response = await self.client.get(f"/notes/{note_id}/sentiment")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Note not found")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.analyze_sentiment.assert_not_called()

    async def test_get_note_sentiment_no_content(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Empty Note", "content": ""}
        self.note_service_mock.get_note.return_value = mock_note

        response = await self.client.get(f"/notes/{note_id}/sentiment")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Note has no content to analyze")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.analyze_sentiment.assert_not_called()

    async def test_summarize_note_valid_id_with_content_gpt4o(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Long Article", "content": "This is a very long article with many details."}
        self.note_service_mock.get_note.return_value = mock_note
        self.note_analysis_service_mock.generate_openai_summary.return_value = {"success": True, "summary": "Short summary."}

        response = await self.client.get(f"/notes/{note_id}/summarize?model=gpt-4o")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "summary": "Short summary."})
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.generate_openai_summary.assert_called_once_with("Long Article", "This is a very long article with many details.", max_length=150, model="gpt-4o")

    async def test_summarize_note_valid_id_with_content_gpt35(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Long Article", "content": "This is a very long article with many details."}
        self.note_service_mock.get_note.return_value = mock_note
        self.note_analysis_service_mock.generate_openai_summary.return_value = {"success": True, "summary": "Another summary."}

        response = await self.client.get(f"/notes/{note_id}/summarize?model=gpt-3.5-turbo")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "summary": "Another summary."})
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.generate_openai_summary.assert_called_once_with("Long Article", "This is a very long article with many details.", max_length=150, model="gpt-3.5-turbo")

    async def test_summarize_note_invalid_id(self):
        response = await self.client.get("/notes/invalid_id/summarize")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid MongoDB ID format")
        self.note_service_mock.get_note.assert_not_called()
        self.note_analysis_service_mock.generate_openai_summary.assert_not_called()

    async def test_summarize_note_not_found(self):
        note_id = str(ObjectId())
        self.note_service_mock.get_note.return_value = None

        response = await self.client.get(f"/notes/{note_id}/summarize")
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Note not found")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.generate_openai_summary.assert_not_called()

    async def test_summarize_note_no_content(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Empty Note", "content": ""}
        self.note_service_mock.get_note.return_value = mock_note

        response = await self.client.get(f"/notes/{note_id}/summarize")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Note has no content to summarize")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.generate_openai_summary.assert_not_called()

    async def test_summarize_note_invalid_model(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Some Note", "content": "Some content."}
        self.note_service_mock.get_note.return_value = mock_note

        response = await self.client.get(f"/notes/{note_id}/summarize?model=invalid-model")
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Model must be either gpt-4o or gpt-3.5-turbo")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.generate_openai_summary.assert_not_called()

    async def test_summarize_note_openai_failure(self):
        note_id = str(ObjectId())
        mock_note = {"_id": ObjectId(note_id), "title": "Some Note", "content": "Some content."}
        self.note_service_mock.get_note.return_value = mock_note
        self.note_analysis_service_mock.generate_openai_summary.return_value = {"success": False, "error": "OpenAI API error"}

        response = await self.client.get(f"/notes/{note_id}/summarize")
        self.assertEqual(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json()["detail"], "OpenAI API error")
        self.note_service_mock.get_note.assert_called_once_with(self.db_mock, note_id=note_id)
        self.note_analysis_service_mock.generate_openai_summary.assert_called_once_with("Some Note", "Some content.", max_length=150, model="gpt-4o")

if __name__ == "__main__":
    unittest.main()