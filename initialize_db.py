import logging
import sys
import os

from app.db.init_mongodb import init_mongodb
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init() -> None:
    """Initialize MongoDB database with collections and indexes"""
    logger.info("Initializing MongoDB database")
    
    if not settings.MONGODB_URI:
        logger.error("MONGODB_URI is not set in environment variables or .env file")
        sys.exit(1)
        
    try:
        init_mongodb()
        logger.info("MongoDB initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        sys.exit(1)

def main() -> None:
    """Main entry point for database initialization"""
    logger.info("Starting database initialization")
    init()
    logger.info("Database initialization finished")

if __name__ == "__main__":
    main()
