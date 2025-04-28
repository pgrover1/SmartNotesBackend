import pytest
from unittest.mock import MagicMock, patch
from bson.objectid import ObjectId

from app.repositories.note_mongodb import NoteMongoRepository
from app.schemas.note import NoteCreate, NoteUpdate

class TestNoteMongoRepository:
    """Tests for the NoteMongoRepository class"""

    def test_init(self):
        """Test repository initialization"""
        repo = NoteMongoRepository()
        assert repo.collection_name == "notes"

    def test_get_notes(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test get_notes method"""
        # Setup mock for get_multi method
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_notes
        repo = NoteMongoRepository()
        result = repo.get_notes(skip=0, limit=10)
        
        # Verify collection find was called
        mock_collection.find.assert_called_once_with()
        
        # Verify the result contains the expected note data
        assert len(result) == 1
        assert result[0]["id"] == str(mongodb_note_with_id["_id"])
        assert result[0]["title"] == mongodb_note_with_id["title"]

    def test_get_note(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test get_note method"""
        # Setup mock for find_one method
        mock_collection.find_one.return_value = mongodb_note_with_id
        
        # Create the repository and call get_note
        repo = NoteMongoRepository()
        result = repo.get_note(str(mongodb_note_with_id["_id"]))
        
        # Verify find_one was called with the correct ObjectId
        mock_collection.find_one.assert_called_once()
        assert mock_collection.find_one.call_args[0][0]["_id"] == mongodb_note_with_id["_id"]
        
        # Verify the result contains the expected note data
        assert result["id"] == str(mongodb_note_with_id["_id"])
        assert result["title"] == mongodb_note_with_id["title"]

    def test_get_notes_by_category(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id, serialized_note):
        """Test get_notes_by_category method"""
        # Setup mock for get_by_filter
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call get_notes_by_category
        repo = NoteMongoRepository()
        category_id = "507f1f77bcf86cd799439011"
        result = repo.get_notes_by_category(category_id, skip=0, limit=10)
        
        # Verify find was called with the correct filter
        mock_collection.find.assert_called_once()
        assert mock_collection.find.call_args[0][0] == {"category_ids": category_id}
        
        # Verify the result contains the expected note data
        assert len(result) == 1
        assert result[0]["id"] == str(mongodb_note_with_id["_id"])
        assert result[0]["title"] == mongodb_note_with_id["title"]

    def test_create_note(self, mock_collection, mock_mongodb_get_collection, serialized_note):
        """Test create_note method"""
        # Setup mocks for insert_one and find_one
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439013"))
        mock_collection.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "title": "Test Note",
            "content": "This is a test note",
            "category_ids": ["507f1f77bcf86cd799439011"],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        # Create test note data
        note_create = NoteCreate(
            title="Test Note",
            content="This is a test note",
            category_ids=["507f1f77bcf86cd799439011"]
        )
        
        # Create the repository and call create_note
        repo = NoteMongoRepository()
        result = repo.create_note(note_create)
        
        # Verify insert_one was called
        assert mock_collection.insert_one.call_count == 1
        
        # Verify the category_ids are handled correctly
        insert_data = mock_collection.insert_one.call_args[0][0]
        assert isinstance(insert_data["category_ids"], list)
        
        # Verify the result contains the expected note data
        assert result["id"] == "507f1f77bcf86cd799439013"
        assert result["title"] == "Test Note"
        assert result["category_ids"] == ["507f1f77bcf86cd799439011"]

    def test_update_note(self, mock_collection, mock_mongodb_get_collection, serialized_note):
        """Test update_note method"""
        # Setup mocks for update_one and find_one
        mock_collection.update_one.return_value = MagicMock(modified_count=1)
        mock_collection.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "title": "Updated Note",
            "content": "This is an updated test note",
            "category_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439022"],
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
        
        # Create test note update data
        note_update = NoteUpdate(
            title="Updated Note",
            content="This is an updated test note",
            category_ids=["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439022"]
        )
        
        # Create the repository and call update_note
        repo = NoteMongoRepository()
        result = repo.update_note("507f1f77bcf86cd799439013", note_update)
        
        # Verify update_one was called with the correct data
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args[0]
        assert call_args[0]["_id"] == ObjectId("507f1f77bcf86cd799439013")
        
        # Verify the category_ids are handled correctly in the update
        set_data = call_args[1]["$set"]
        assert isinstance(set_data["category_ids"], list)
        assert len(set_data["category_ids"]) == 2
        
        # Verify the result contains the expected note data
        assert result["id"] == "507f1f77bcf86cd799439013"
        assert result["title"] == "Updated Note"
        assert result["content"] == "This is an updated test note"
        assert result["category_ids"] == ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439022"]

    def test_delete_note(self, mock_collection, mock_mongodb_get_collection):
        """Test delete_note method"""
        # Setup mock for delete_one
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)
        
        # Create the repository and call delete_note
        repo = NoteMongoRepository()
        result = repo.delete_note("507f1f77bcf86cd799439013")
        
        # Verify delete_one was called with the correct ObjectId
        mock_collection.delete_one.assert_called_once()
        assert mock_collection.delete_one.call_args[0][0]["_id"] == ObjectId("507f1f77bcf86cd799439013")
        
        # Verify the result is True when document was deleted
        assert result is True
        
    def test_search_notes_keyword_only(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id):
        """Test search_notes method with keyword only"""
        # Setup mock for find
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call search_notes with keyword
        repo = NoteMongoRepository()
        result = repo.search_notes(keyword="test", skip=0, limit=10)
        
        # Verify find was called with the correct regex filter
        mock_collection.find.assert_called_once()
        filter_dict = mock_collection.find.call_args[0][0]
        assert "$or" in filter_dict
        assert len(filter_dict["$or"]) == 2
        
        # Verify the regex expressions are correct
        title_filter = filter_dict["$or"][0]
        content_filter = filter_dict["$or"][1]
        assert title_filter["title"]["$regex"] == "test"
        assert title_filter["title"]["$options"] == "i"
        assert content_filter["content"]["$regex"] == "test"
        assert content_filter["content"]["$options"] == "i"
        
    def test_search_notes_category_only(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id):
        """Test search_notes method with category only"""
        # Setup mock for find
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call search_notes with category
        repo = NoteMongoRepository()
        category_id = "507f1f77bcf86cd799439011"
        result = repo.search_notes(category_id=category_id, skip=0, limit=10)
        
        # Verify find was called with the correct category filter
        mock_collection.find.assert_called_once()
        filter_dict = mock_collection.find.call_args[0][0]
        assert "category_ids" in filter_dict
        assert filter_dict["category_ids"] == category_id
        
    def test_search_notes_both_filters(self, mock_collection, mock_mongodb_get_collection, mongodb_note_with_id):
        """Test search_notes method with both keyword and category"""
        # Setup mock for find
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = [mongodb_note_with_id]
        mock_collection.find.return_value = mock_cursor
        
        # Create the repository and call search_notes with both filters
        repo = NoteMongoRepository()
        category_id = "507f1f77bcf86cd799439011"
        result = repo.search_notes(keyword="test", category_id=category_id, skip=0, limit=10)
        
        # Verify find was called with combined filters
        mock_collection.find.assert_called_once()
        filter_dict = mock_collection.find.call_args[0][0]
        assert "$or" in filter_dict
        assert "category_ids" in filter_dict
        assert filter_dict["category_ids"] == category_id