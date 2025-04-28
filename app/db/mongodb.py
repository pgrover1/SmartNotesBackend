import ssl
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
from pymongo.database import Database
from app.core.config import settings
from bson.objectid import ObjectId

# MongoDB client instance
_client = None

def get_client() -> MongoClient:
    """Get MongoDB client instance"""
    global _client
    if not _client:
        if not settings.MONGODB_URI:
            raise ValueError("MONGODB_URI is not set in environment variables")
        
        _client = MongoClient(settings.MONGODB_URI, server_api=ServerApi('1'),    tlsCAFile=certifi.where(),
    ssl_match_hostname=True, ssl_cert_reqs=ssl.CERT_REQUIRED)
        
        # Test connection
        try:
            _client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            raise
    
    return _client

def get_database() -> Database:
    """Get MongoDB database instance"""
    client = get_client()
    return client[settings.MONGODB_DB_NAME]

def get_collection(collection_name: str) -> Collection:
    """Get MongoDB collection"""
    db = get_database()
    return db[collection_name]

# Dependency to get MongoDB database
def get_db():
    """Dependency for getting MongoDB database"""
    try:
        db = get_database()
        yield db
    except ValueError as e:
        # For tests when MongoDB is not configured
        print(f"MongoDB dependency error (expected in tests): {e}")
        yield None

# Utility functions for MongoDB
def serialize_id(item):
    """Convert MongoDB _id to string"""
    if item and "_id" in item and isinstance(item["_id"], ObjectId):
        item["id"] = str(item["_id"])
        del item["_id"]
    return item

def prepare_for_mongo(data):
    """Prepare data for MongoDB insertion"""
    if data and "id" in data:
        # If converting from SQLAlchemy models
        del data["id"]
    return data