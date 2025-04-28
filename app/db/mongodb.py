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
        # Try simple connection first
        if not settings.MONGODB_URI:
            raise ValueError("MONGODB_URI is not set in environment variables")
        
        print("Attempting to connect to MongoDB...")
        try:
            from pymongo import monitoring
            
            # Define an event listener for server heartbeat events
            class ServerHeartbeatListener(monitoring.ServerHeartbeatListener):
                def started(self, event):
                    print(f"Server heartbeat started to {event.connection_id}")
                
                def succeeded(self, event):
                    print(f"Server heartbeat to {event.connection_id} succeeded")
                
                def failed(self, event):
                    print(f"Server heartbeat to {event.connection_id} failed with error: {event.reply}")
            
            # Register the listener
            monitoring.register(ServerHeartbeatListener())
            
            # Basic connection with minimal options and no SRV resolution
            print(f"Connecting to: {settings.MONGODB_URI}")
            
            # Try standard connection
            _client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=10000
            )
            
            # Test connection
            _client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            return _client
        except Exception as e:
            import traceback
            # If first attempt fails, try localhost
            print(f"MongoDB connection error: {e}")
            traceback.print_exc()
            
            # Try with a completely different approach - no SRV, single node, simple URI
            try:
                print("Trying non-SRV direct connection...")
                
                # Create a simple non-SRV connection URI
                simple_uri = "mongodb://piyushgrover15:k44ucp0VW4et9ofH@ac-iykme4n-shard-00-00.m9bfj9w.mongodb.net:27017,ac-iykme4n-shard-00-01.m9bfj9w.mongodb.net:27017,ac-iykme4n-shard-00-02.m9bfj9w.mongodb.net:27017/notes_app?authSource=admin&replicaSet=atlas-m4fcbp-shard-0&ssl=true"
                
                _client = MongoClient(simple_uri, ssl=True)
                _client.admin.command('ping')
                print("Successfully connected using non-SRV URI!")
                return _client
            except Exception as alter_error:
                print(f"Non-SRV connection failed: {alter_error}")
                
                # Try a direct connection to specific shard
                try:
                    print("Trying direct connection to single MongoDB Atlas shard...")
                    
                    # Direct connection to a single shard
                    direct_uri = "mongodb://piyushgrover15:k44ucp0VW4et9ofH@ac-iykme4n-shard-00-00.m9bfj9w.mongodb.net:27017/?authSource=admin&ssl=true"
                    
                    _client = MongoClient(
                        direct_uri,
                        serverSelectionTimeoutMS=5000,
                        ssl=True,
                        directConnection=True  # Use a direct connection
                    )
                    _client.admin.command('ping')
                    print("Successfully connected to MongoDB Atlas shard!")
                    return _client
                except Exception as direct_error:
                    print(f"Direct shard connection failed: {direct_error}")
            
                # Try local MongoDB as final fallback
                try:
                    print("Trying fallback to local MongoDB...")
                    _client = MongoClient('mongodb://localhost:27017/')
                    _client.admin.command('ping')
                    print("Successfully connected to local MongoDB!")
                    return _client
                except Exception as local_error:
                    print(f"Local MongoDB connection failed: {local_error}")
                    
                    # All attempts failed, raise original error
                    print("All MongoDB connection attempts failed")
                    raise e
    
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