import pytest
from unittest.mock import patch, MagicMock
from app.services.ai import AIService
from app.services.notes import NoteService
from app.models.note import Note
from app.models.category import Category

# Test the auto-categorization feature

def test_suggest_category_zero_shot():
    """Test category suggestion using zero-shot classification"""
    # Create mock AI service
    ai_service = AIService()
    ai_service.is_enabled = True
    
    # Mock zero-shot model
    mock_zero_shot = MagicMock()
    mock_zero_shot.return_value = {
        "sequence": "This is a work note about meetings",
        "labels": ["Work", "Personal", "Ideas"],
        "scores": [0.8, 0.1, 0.1]
    }
    ai_service.models = {"zero_shot": mock_zero_shot}
    
    # Test category suggestion
    categories = [(1, "Work"), (2, "Personal"), (3, "Ideas")]
    result = ai_service.suggest_category("This is a work note about meetings", categories)
    
    # Should return the ID of the Work category
    assert result == 1

@pytest.fixture
def mock_categorization_service():
    mock_service = MagicMock()
    mock_service.suggest_category.return_value = {
        "category": "Work", 
        "confidence": 0.85
    }
    return mock_service

@pytest.fixture
def mock_note_repository():
    mock_repo = MagicMock()
    mock_repo.get_note.return_value = {
        "id": "1", 
        "title": "Meeting Notes", 
        "content": "Notes from the work meeting", 
        "category_ids": []
    }
    mock_repo.update_note.return_value = {
        "id": "1", 
        "title": "Meeting Notes", 
        "content": "Notes from the work meeting", 
        "category_ids": ["123"]
    }
    return mock_repo

@pytest.fixture
def mock_category_repository():
    mock_repo = MagicMock()
    mock_repo.get_categories.return_value = [
        {"id": "123", "name": "Work"},
        {"id": "456", "name": "Personal"},
    ]
    return mock_repo

def test_note_auto_categorization():
    """Test automatic categorization when creating a note"""
    # Create a note service with mocked dependencies
    note_service = NoteService()
    
    # Mock the _apply_ai_enhancements method
    note_service._apply_ai_enhancements = lambda db, data: {
        **data,
        "summary": "Mocked summary",
        "sentiment": "Positive"
    }
    
    # Mock the ai_service.suggest_category method
    note_service.ai_service = MagicMock()
    note_service.ai_service.suggest_category = lambda text, categories: 1 if "work" in text.lower() else None
    
    # Mock database session
    db = MagicMock()
    
    # Mock Category query
    mock_category = MagicMock(spec=Category)
    mock_category.id = 1
    mock_category.name = "Work"
    db.query.return_value.filter.return_value.first.return_value = mock_category
    db.query.return_value.all.return_value = [mock_category]
    
    # Mock repository create method to return a note
    mock_note = MagicMock(spec=Note)
    mock_note.id = 1
    mock_note.title = "Test Note"
    mock_note.content = "This is a work-related test note"
    mock_note.categories = []
    
    # Setup the mock for note repository
    note_service.note_repository = MagicMock()
    note_service.note_repository.create_with_categories = lambda db, obj_in: mock_note
    
    # Create note without explicit categories
    from app.schemas.note import NoteCreate
    note_in = NoteCreate(
        title="Test Note",
        content="This is a work-related test note",
        category_ids=[]
    )
    
    # Call the method
    result = note_service.create_note(db, note_in)
    
    # Verify the result
    assert result == mock_note
    # Verify that the category was added
    db.add.assert_called_once_with(mock_note)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(mock_note)