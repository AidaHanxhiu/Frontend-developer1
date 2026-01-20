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
def create_genre(name, description=None):
    """Create a new genre"""
    db = get_db()
    
    # Check if genre exists
    existing = db.genres.find_one({"name": name})
    if existing:
        return existing
    
    genre = {
        "name": name,
        "description": description,
        "created_at": datetime.utcnow()
    }
    
    result = db.genres.insert_one(genre)
    genre["_id"] = result.inserted_id
    return genre


# ---------- READ ----------
def get_all_genres():
    """Get all genres"""
    db = get_db()
    return list(db.genres.find({}))


def get_genre_by_id(genre_id):
    """Get genre by ID"""
    db = get_db()
    try:
        return db.genres.find_one({"_id": ObjectId(genre_id)})
    except:
        return None


def get_genre_by_name(name):
    """Get genre by name"""
    db = get_db()
    return db.genres.find_one({"name": name})


# ---------- UPDATE ----------
def update_genre(genre_id, update_data):
    """Update genre information"""
    db = get_db()
    try:
        result = db.genres.update_one(
            {"_id": ObjectId(genre_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


# ---------- DELETE ----------
def delete_genre(genre_id):
    """Delete a genre"""
    db = get_db()
    try:
        result = db.genres.delete_one({"_id": ObjectId(genre_id)})
        return result.deleted_count > 0
    except:
        return False