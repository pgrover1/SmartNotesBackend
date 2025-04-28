import pytest
from unittest.mock import MagicMock, patch
from app.db.init_mongodb import init_mongodb

class TestInitMongoDB:
    """Tests for MongoDB initialization"""

    def test_init_mongodb_existing_collections(self):
        """Test initialization when collections already exist"""
        # Mock database
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = ["notes", "categories"]
        
        # Mock notes and categories collections
        mock_notes = MagicMock()
        mock_categories = MagicMock()
        
        # Attach collections to db
        mock_db.notes = mock_notes
        mock_db.categories = mock_categories
        
        # Mock existing categories (no default categories should be created)
        mock_db.categories.count_documents.return_value = 5
        
        # Patch get_database to return our mock
        with patch('app.db.init_mongodb.get_database', return_value=mock_db):
            # Call the initialization function
            init_mongodb()
            
            # Verify collections were not created
            mock_db.create_collection.assert_not_called()
            
            # Verify indexes were created
            mock_notes.create_index.assert_called()
            mock_categories.create_index.assert_called()
            
            # Verify default categories were not inserted
            mock_db.categories.insert_many.assert_not_called()

    def test_init_mongodb_new_collections(self):
        """Test initialization when collections need to be created"""
        # Mock database
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = []
        
        # Mock notes and categories collections
        mock_notes = MagicMock()
        mock_categories = MagicMock()
        
        # Attach collections to db
        mock_db.notes = mock_notes
        mock_db.categories = mock_categories
        
        # Mock empty categories collection (default categories should be created)
        mock_db.categories.count_documents.return_value = 0
        
        # Patch get_database to return our mock
        with patch('app.db.init_mongodb.get_database', return_value=mock_db):
            # Call the initialization function
            init_mongodb()
            
            # Verify collections were created
            assert mock_db.create_collection.call_count == 2
            mock_db.create_collection.assert_any_call("notes")
            mock_db.create_collection.assert_any_call("categories")
            
            # Verify indexes were created
            mock_notes.create_index.assert_called()
            mock_categories.create_index.assert_called()
            
            # Verify default categories were inserted
            mock_db.categories.insert_many.assert_called_once()
            # Verify it inserted 5 default categories
            inserted_categories = mock_db.categories.insert_many.call_args[0][0]
            assert len(inserted_categories) == 5
            
            # Verify category names
            category_names = [cat["name"] for cat in inserted_categories]
            assert "Work" in category_names
            assert "Personal" in category_names
            assert "Study" in category_names
            assert "Ideas" in category_names
            assert "To-Do" in category_names

    def test_index_creation(self):
        """Test that all required indexes are created"""
        # Mock database
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = ["notes", "categories"]
        
        # Mock notes and categories collections
        mock_notes = MagicMock()
        mock_categories = MagicMock()
        
        # Attach collections to db
        mock_db.notes = mock_notes
        mock_db.categories = mock_categories
        
        # Mock existing categories
        mock_db.categories.count_documents.return_value = 5
        
        # Patch get_database to return our mock
        with patch('app.db.init_mongodb.get_database', return_value=mock_db):
            # Call the initialization function
            init_mongodb()
            
            # Verify notes indexes
            assert mock_notes.create_index.call_count == 4
            mock_notes.create_index.assert_any_call("created_at")
            mock_notes.create_index.assert_any_call("title")
            mock_notes.create_index.assert_any_call(["title", "content"], name="text_search", background=True)
            mock_notes.create_index.assert_any_call("category_ids")
            
            # Verify categories indexes
            assert mock_categories.create_index.call_count == 2
            mock_categories.create_index.assert_any_call("name", unique=True)
            mock_categories.create_index.assert_any_call("created_at")