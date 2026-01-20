from werkzeug.security import generate_password_hash, check_password_hash
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
def create_user(first_name, last_name, email, password, role="student"):
    """Create a new user"""
    db = get_db()
    
    # Check if user already exists
    if get_user_by_email(email):
        return None
    
    user = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": generate_password_hash(password),
        "role": role,
        "created_at": datetime.utcnow()
    }
    
    result = db.users.insert_one(user)
    user["_id"] = result.inserted_id
    user.pop("password")  # Don't return password
    return user


# ---------- READ ----------
def get_user_by_email(email):
    """Get user by email"""
    db = get_db()
    return db.users.find_one({"email": email})


def get_user_by_id(user_id):
    """Get user by ID"""
    db = get_db()
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user.pop("password", None)
        return user
    except:
        return None


def get_all_users():
    """Get all users"""
    db = get_db()
    users = list(db.users.find({}))
    for user in users:
        user.pop("password", None)
    return users


# ---------- UPDATE ----------
def update_user(user_id, update_data):
    """Update user information"""
    db = get_db()
    try:
        # Don't allow password updates through this function
        update_data.pop("password", None)
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


def update_user_password(user_id, new_password):
    """Update user password"""
    db = get_db()
    try:
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": generate_password_hash(new_password)}}
        )
        return result.modified_count > 0
    except:
        return False


# ---------- DELETE ----------
def delete_user(user_id):
    """Delete a user"""
    db = get_db()
    try:
        result = db.users.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    except:
        return False


# ---------- AUTHENTICATION ----------
def verify_user(email, password):
    """Verify user credentials"""
    user = get_user_by_email(email)
    if user and check_password_hash(user["password"], password):
        user.pop("password")
        return user
    return None