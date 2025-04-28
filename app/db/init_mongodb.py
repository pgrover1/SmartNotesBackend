from app.db.mongodb import get_database
from datetime import datetime

def init_mongodb():
    """Initialize MongoDB collections with indexes"""
    db = get_database()
    
    # Create collections if they don't exist
    if "notes" not in db.list_collection_names():
        db.create_collection("notes")
    
    if "categories" not in db.list_collection_names():
        db.create_collection("categories")
    
    # Create indexes
    db.notes.create_index("created_at")
    db.notes.create_index("title")
    db.notes.create_index(["title", "content"], name="text_search", background=True)
    db.notes.create_index("category_ids")
    
    db.categories.create_index("name", unique=True)
    db.categories.create_index("created_at")
    
    print("MongoDB collections and indexes created successfully")
    
    # Add default categories if none exist
    if db.categories.count_documents({}) == 0:
        default_categories = [
            {"name": "Work", "description": "Work-related notes", "created_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}, "updated_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}},
            {"name": "Personal", "description": "Personal notes", "created_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}, "updated_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}},
            {"name": "Study", "description": "Study-related notes", "created_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}, "updated_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}},
            {"name": "Ideas", "description": "Ideas and brainstorming", "created_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}, "updated_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}},
            {"name": "To-Do", "description": "Tasks and to-do items", "created_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}, "updated_at": {"$date": {"$numberLong": str(int(datetime.utcnow().timestamp() * 1000))}}}
        ]
        
        db.categories.insert_many(default_categories)
        print(f"Added {len(default_categories)} default categories")

# Run if executed directly
if __name__ == "__main__":
    init_mongodb()
