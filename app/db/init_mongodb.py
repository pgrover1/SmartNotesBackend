from app.db.mongodb import get_database
from datetime import datetime

def init_mongodb():
    """Initialize MongoDB collections with indexes"""
    db = get_database()
    print("Initializing MongoDB collections and indexes")
    # Create collections if they don't exist
    if "notes" not in db.list_collection_names():
        db.create_collection("notes")
    
    if "categories" not in db.list_collection_names():
        db.create_collection("categories")
    # Create indexes if they don't exist
    def ensure_index(collection, index_key, **kwargs):
        """Create index if it doesn't exist already"""
        existing_indexes = collection.index_information()
        
        # Convert index_key to string for comparison
        if isinstance(index_key, list):
            index_name = "_".join([f"{k}_1" for k in index_key])
        else:
            index_name = f"{index_key}_1"
            
        # Check if name was specified
        if "name" in kwargs:
            index_name = kwargs["name"]
        
        # Check if index already exists
        if index_name in existing_indexes or f"{index_name}" in existing_indexes:
            print(f"Index {index_name} already exists, skipping...")
        else:
            print(f"Creating index {index_name}...")
            collection.create_index(index_key, **kwargs)
    
    # Notes collection indexes
    ensure_index(db.notes, "created_at")
    ensure_index(db.notes, "title")
    ensure_index(db.notes, "category_ids")
    
    # Categories collection indexes
    ensure_index(db.categories, "name", unique=True)
    ensure_index(db.categories, "created_at")
    
    print("MongoDB collections and indexes created successfully")
    
    # Add default categories if none exist
    if db.categories.count_documents({}) == 0:
        # Use simple datetime objects instead of complex structures
        now = datetime.utcnow()
        default_categories = [
            {"name": "Work", "description": "Work-related notes", "created_at": now, "updated_at": now},
            {"name": "Personal", "description": "Personal notes", "created_at": now, "updated_at": now}
           ]
        
        db.categories.insert_many(default_categories)
        print(f"Added {len(default_categories)} default categories")

# Run if executed directly
if __name__ == "__main__":
    init_mongodb()
