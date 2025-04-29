import os
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from pymongo.collection import Collection
from bson.objectid import ObjectId

from app.db.base import Base
from app.main import app
from app.db.session import get_db as sqlalchemy_get_db
from app.db.mongodb import get_db as mongodb_get_db

# Use an in-memory SQLite database for testing SQLAlchemy
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a new SQLite in-memory database engine for tests"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    # Clean up the database after tests
    Base.metadata.drop_all(bind=engine)
    # Remove the test database file if it exists
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """Create a new database session for a test"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    
    # Use a sessionmaker to create a new session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    
    yield session
    
    # Rollback the transaction and close the session after the test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the FastAPI app with the test database"""
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[sqlalchemy_get_db] = override_get_db
    app.dependency_overrides[mongodb_get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Reset the dependency override
    app.dependency_overrides = {}

## MongoDB Test Fixtures ##

@pytest.fixture
def mock_collection():
    """Create a mock MongoDB collection"""
    mock_coll = MagicMock(spec=Collection)
    return mock_coll

@pytest.fixture
def mock_mongodb_get_collection(mock_collection):
    """Patch the get_collection function to return a mock collection"""
    with patch("app.db.mongodb.get_collection", return_value=mock_collection) as mock_get_collection:
        yield mock_get_collection

@pytest.fixture
def sample_note_data():
    """Sample note data for testing"""
    return {
        "title": "Test Note",
        "content": "This is a test note",
        "category_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"],
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def sample_category_data():
    """Sample category data for testing"""
    return {
        "name": "Test Category",
        "description": "This is a test category",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }

@pytest.fixture
def mongodb_note_with_id(sample_note_data):
    """Sample note data with MongoDB ObjectId"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439013"),
        **sample_note_data
    }

@pytest.fixture
def mongodb_category_with_id(sample_category_data):
    """Sample category data with MongoDB ObjectId"""
    return {
        "_id": ObjectId("507f1f77bcf86cd799439014"),
        **sample_category_data
    }

@pytest.fixture
def serialized_note(mongodb_note_with_id):
    """Note with serialized id for testing"""
    note = dict(mongodb_note_with_id)
    note["id"] = str(note.pop("_id"))
    return note

@pytest.fixture
def serialized_category(mongodb_category_with_id):
    """Category with serialized id for testing"""
    category = dict(mongodb_category_with_id)
    category["id"] = str(category.pop("_id"))
    return category

## AI Service Mocks ##

@pytest.fixture
def mock_ai_services():
    """Mock all AI services"""
    mock_categorization = MagicMock()
    mock_categorization.suggest_category.return_value = {
        "category": "Work",
        "confidence": 0.9,
        "keywords": ["meeting", "work", "notes"],
        "method": "openai"
    }
    
    mock_note_analysis = MagicMock()
    mock_note_analysis.generate_openai_summary.return_value = {
        "summary": "A test note summary",
        "success": True,
        "error": None,
        "model_used": "gpt-4o"
    }
    mock_note_analysis.analyze_sentiment.return_value = "Positive"
    
    services = {
        "categorization": mock_categorization,
        "note_analysis": mock_note_analysis
    }
    
    with patch('app.services.factory_ai.get_ai_services', return_value=services):
        yield services