import logging
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine
from app.core.config import settings
from app.models.category import Category

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default categories to create
DEFAULT_CATEGORIES = [
    {"name": "Work", "description": "Work-related notes and tasks"},
    {"name": "Personal", "description": "Personal notes and reminders"},
    {"name": "Ideas", "description": "Creative ideas and concepts"},
    {"name": "Learning", "description": "Educational content and learning notes"},
    {"name": "Meetings", "description": "Meeting notes and summaries"}
]

def init_db(db: Session) -> None:
    """Initialize the database with tables and default data"""
    # Create tables
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    
    # Add default categories if they don't exist
    for category_data in DEFAULT_CATEGORIES:
        existing_category = db.query(Category).filter(Category.name == category_data["name"]).first()
        if not existing_category:
            category = Category(**category_data)
            db.add(category)
    
    db.commit()
    logger.info("Database initialized with default data")
