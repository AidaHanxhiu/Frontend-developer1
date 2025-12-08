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
def create_request(user_id, book_title, author=None, reason=None):
    """Create a new book request"""
    db = get_db()
    
    request = {
        "user_id": ObjectId(user_id),
        "book_title": book_title,
        "author": author,
        "reason": reason,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    result = db.requests.insert_one(request)
    request["_id"] = result.inserted_id
    return request


# ---------- READ ----------
def get_all_requests():
    """Get all requests"""
    db = get_db()
    return list(db.requests.find({}))


def get_request_by_id(request_id):
    """Get request by ID"""
    db = get_db()
    try:
        return db.requests.find_one({"_id": ObjectId(request_id)})
    except:
        return None


def get_user_requests(user_id):
    """Get all requests for a user"""
    db = get_db()
    try:
        return list(db.requests.find({"user_id": ObjectId(user_id)}))
    except:
        return []


# ---------- UPDATE ----------
def update_request_status(request_id, status):
    """Update request status (pending, approved, rejected)"""
    db = get_db()
    try:
        result = db.requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    except:
        return False


# ---------- DELETE ----------
def delete_request(request_id):
    """Delete a request"""
    db = get_db()
    try:
        result = db.requests.delete_one({"_id": ObjectId(request_id)})
        return result.deleted_count > 0
    except:
        return False

