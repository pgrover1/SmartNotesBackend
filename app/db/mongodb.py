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
        
        # Simple approach with minimal options to avoid conflicts
        try:
            # Create a client with minimal options first
            _client = MongoClient(
                settings.MONGODB_URI,
                server_api=ServerApi('1')
            )
            
            # Test connection
            _client.admin.command('ping')
            print("Successfully connected to MongoDB!")
        except Exception as e:
            import traceback
            print(f"MongoDB connection error: {e}")
            print(f"TLS/SSL info: using certifi path {certifi.where()}")
            print(f"MongoDB URI: {settings.MONGODB_URI.split('@')[0].split('://')[0]}://*****@{settings.MONGODB_URI.split('@')[1] if '@' in settings.MONGODB_URI else '(no credentials)'}")
            print(f"Python SSL version: {ssl.OPENSSL_VERSION}")
            traceback.print_exc()
            
            # Try alternative approaches if the first attempt failed
            try:
                print("Attempting connection with tlsCAFile parameter...")
                _client = MongoClient(
                    settings.MONGODB_URI,
                    server_api=ServerApi('1'),
                    tlsCAFile=certifi.where()
                )
                _client.admin.command('ping')
                print("Successfully connected to MongoDB with tlsCAFile!")
                return _client
            except Exception as second_error:
                print(f"Second connection attempt failed: {second_error}")
                
                # Try with direct connection (bypass SRV lookup issues)
                try:
                    print("Attempting connection with DirectConnection...")
                    _client = MongoClient(
                        settings.MONGODB_URI,
                        server_api=ServerApi('1'),
                        directConnection=True
                    )
                    _client.admin.command('ping')
                    print("Successfully connected to MongoDB with DirectConnection!")
                    return _client
                except Exception as direct_error:
                    print(f"Direct connection attempt failed: {direct_error}")
                    
                    # Final fallback with reduced security (only use in development)
                    try:
                        print("Attempting final fallback connection with reduced security...")
                        # Add tlsAllowInvalidCertificates=true to the URI
                        uri_parts = settings.MONGODB_URI.split('?')
                        base_uri = uri_parts[0]
                        query_params = uri_parts[1] if len(uri_parts) > 1 else ""
                        if query_params:
                            fallback_uri = f"{base_uri}?tlsAllowInvalidCertificates=true&{query_params}"
                        else:
                            fallback_uri = f"{base_uri}?tlsAllowInvalidCertificates=true"
                        
                        _client = MongoClient(fallback_uri, server_api=ServerApi('1'))
                        _client.admin.command('ping')
                        print("Successfully connected to MongoDB with fallback URI!")
                        print("WARNING: Using reduced security settings. Fix your certificates for production use.")
                        return _client
                    except Exception as fallback_error:
                        print(f"All connection attempts failed: {fallback_error}")
                        
                        # Final last-ditch attempt with non-SRV connection to specific server
                        try:
                            # If URI is SRV format, try direct connection to first shard
                            if "mongodb+srv" in settings.MONGODB_URI:
                                print("Attempting connection with direct server address...")
                                # Extract domain from SRV URI and connect to first shard directly
                                parsed_uri = settings.MONGODB_URI.split('@')
                                if len(parsed_uri) >= 2:
                                    credentials = parsed_uri[0]
                                    domain_part = parsed_uri[1].split('/')[0]
                                    # Replace domain with first shard address
                                    direct_uri = f"{credentials}@ac-iykme4n-shard-00-00.{domain_part}:27017/?ssl=true&authSource=admin&replicaSet=atlas-m4fcbp-shard-0&tlsAllowInvalidCertificates=true"
                                    print(f"Trying direct URI: {direct_uri.split('@')[0]}://*****@{direct_uri.split('@')[1]}")
                                    _client = MongoClient(direct_uri)
                                    _client.admin.command('ping')
                                    print("Successfully connected to MongoDB with direct server address!")
                                    return _client
                                else:
                                    print("Could not parse URI for direct connection")
                        except Exception as direct_server_error:
                            print(f"Direct server connection failed: {direct_server_error}")
            
            # If all attempts failed, raise the original error
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