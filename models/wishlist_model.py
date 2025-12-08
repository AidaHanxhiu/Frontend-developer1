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
def add_to_wishlist(user_id, book_id):
    """Add a book to user's wishlist"""
    db = get_db()
    
    # Check if already in wishlist
    existing = db.wishlist.find_one({
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id)
    })
    
    if existing:
        return existing
    
    wishlist_item = {
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id),
        "added_at": datetime.utcnow()
    }
    
    result = db.wishlist.insert_one(wishlist_item)
    wishlist_item["_id"] = result.inserted_id
    return wishlist_item


# ---------- READ ----------
def get_user_wishlist(user_id):
    """Get user's wishlist"""
    db = get_db()
    try:
        return list(db.wishlist.find({"user_id": ObjectId(user_id)}))
    except:
        return []


def is_in_wishlist(user_id, book_id):
    """Check if book is in user's wishlist"""
    db = get_db()
    try:
        return db.wishlist.find_one({
            "user_id": ObjectId(user_id),
            "book_id": ObjectId(book_id)
        }) is not None
    except:
        return False


# ---------- DELETE ----------
def remove_from_wishlist(user_id, book_id):
    """Remove a book from user's wishlist"""
    db = get_db()
    try:
        result = db.wishlist.delete_one({
            "user_id": ObjectId(user_id),
            "book_id": ObjectId(book_id)
        })
        return result.deleted_count > 0
    except:
        return False

