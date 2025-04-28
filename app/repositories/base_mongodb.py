from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from bson.objectid import ObjectId
from app.db.mongodb import get_collection, serialize_id, prepare_for_mongo

T = TypeVar('T')

class BaseMongoRepository(Generic[T]):
    """Base repository for MongoDB operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    @property
    def collection(self):
        return get_collection(self.collection_name)
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all items with pagination"""
        cursor = self.collection.find().sort("created_at", -1).skip(skip).limit(limit)
        return [serialize_id(item) for item in cursor]
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        item = self.collection.find_one({"_id": ObjectId(id)})
        return serialize_id(item) if item else None
    
    def get_by_filter(self, filter_dict: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Find items matching filter criteria"""
        cursor = self.collection.find(filter_dict).sort("created_at", -1).skip(skip).limit(limit)
        return [serialize_id(item) for item in cursor]
    
    def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item"""
        obj_data = prepare_for_mongo(obj_in.copy() if isinstance(obj_in, dict) else obj_in.dict())
        
        # Add timestamps
        from datetime import datetime
        now = datetime.utcnow()
        obj_data["created_at"] = now
        obj_data["updated_at"] = now
        
        result = self.collection.insert_one(obj_data)
        return self.get(str(result.inserted_id))
    
    def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing item"""
        obj_data = obj_in.copy() if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        obj_data = {k: v for k, v in obj_data.items() if v is not None}
        
        # Update timestamp
        from datetime import datetime
        obj_data["updated_at"] = datetime.utcnow()
        
        self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": obj_data}
        )
        return self.get(id)
    
    def remove(self, id: str) -> bool:
        """Delete an item"""
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count items matching filter criteria"""
        if filter_dict:
            return self.collection.count_documents(filter_dict)
        return self.collection.count_documents({})
