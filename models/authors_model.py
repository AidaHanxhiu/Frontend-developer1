from bson import ObjectId
from datetime import datetime


def get_db():
    """Get database connection"""
    from pymongo import MongoClient
    import os
    from dotenv import load_dotenv
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is not set. Please check your .env file.")
    # Remove quotes if present
    mongodb_uri = mongodb_uri.strip().strip('"').strip("'")
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    return client["library"]


# ---------- CREATE ----------
def create_author(name, bio=None):
    """Create a new author"""
    db = get_db()
    
    # Check if author exists
    existing = db.authors.find_one({"name": name})
    if existing:
        return existing
    
    author = {
        "name": name,
        "bio": bio,
        "created_at": datetime.utcnow()
    }
    
    result = db.authors.insert_one(author)
    author["_id"] = result.inserted_id
    return author


# ---------- READ ----------
def get_all_authors():
    """Get all authors"""
    db = get_db()
    return list(db.authors.find({}))


def get_author_by_id(author_id):
    """Get author by ID"""
    db = get_db()
    try:
        return db.authors.find_one({"_id": ObjectId(author_id)})
    except:
        return None


def get_author_by_name(name):
    """Get author by name"""
    db = get_db()
    return db.authors.find_one({"name": name})


# ---------- UPDATE ----------
def update_author(author_id, update_data):
    """Update author information"""
    db = get_db()
    try:
        result = db.authors.update_one(
            {"_id": ObjectId(author_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


# ---------- DELETE ----------
def delete_author(author_id):
    """Delete an author"""
    db = get_db()
    try:
        result = db.authors.delete_one({"_id": ObjectId(author_id)})
        return result.deleted_count > 0
    except:
        return False

