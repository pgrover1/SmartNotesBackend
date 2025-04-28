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
        
        # Better check for existing indexes by looking at their key patterns
        index_exists = False
        for idx_name, idx_info in existing_indexes.items():
            # Check if the key pattern matches
            key_pattern = idx_info.get('key', [])
            if key_pattern:
                if isinstance(index_key, list):
                    # For compound indexes
                    is_match = all(any(k[0] == field for k in key_pattern) for field in index_key)
                else:
                    # For single field indexes
                    is_match = any(k[0] == index_key for k in key_pattern)
                
                if is_match:
                    index_exists = True
                    print(f"Index on {index_key} already exists as {idx_name}, skipping...")
                    break
        
        if not index_exists:
            print(f"Creating index {index_name}...")
            try:
                collection.create_index(index_key, **kwargs)
            except Exception as e:
                print(f"Error creating index {index_name}: {e}")
    
    # Notes collection indexes
    ensure_index(db.notes, "created_at")
    ensure_index(db.notes, "title")
    ensure_index(db.notes, "category_ids")
    
    # Categories collection indexes
    ensure_index(db.categories, "name", unique=True)
    ensure_index(db.categories, "created_at")
    
    print("MongoDB collections and indexes created successfully")
    
    # Add default categories if they don't exist
    # Use simple datetime objects instead of complex structures
    now = datetime.utcnow()
    default_categories = [
        {"name": "Work", "description": "Work-related notes", "created_at": now, "updated_at": now},
        {"name": "Personal", "description": "Personal notes", "created_at": now, "updated_at": now},
    ]
    
    # Insert categories one by one, checking if they exist first
    categories_added = 0
    for category in default_categories:
        if db.categories.count_documents({"name": category["name"]}) == 0:
            try:
                db.categories.insert_one(category)
                categories_added += 1
                print(f"Added category: {category['name']}")
            except Exception as e:
                print(f"Error adding category {category['name']}: {e}")
    
    if categories_added > 0:
        print(f"Added {categories_added} default categories")
    else:
        print("No new default categories needed")

# Run if executed directly
if __name__ == "__main__":
    init_mongodb()
