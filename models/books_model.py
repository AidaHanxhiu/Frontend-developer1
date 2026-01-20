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
def create_book(data):
    """Create a new book"""
    db = get_db()
    
    book = {
        "title": data.get("title", ""),
        "author": data.get("author", ""),
        "year": data.get("year"),
        "isbn": data.get("isbn", ""),
        "description": data.get("description", ""),
        "genre": data.get("genre", ""),
        "language": data.get("language", "English"),
        "available": data.get("available", True),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.books.insert_one(book)
    book["_id"] = result.inserted_id
    return book


# ---------- READ ----------
def get_all_books():
    """Get all books"""
    db = get_db()
    return list(db.books.find({}))


def get_book_by_id(book_id):
    """Get book by ID"""
    db = get_db()
    try:
        return db.books.find_one({"_id": ObjectId(book_id)})
    except:
        return None


def get_books_by_genre(genre):
    """Get books by genre"""
    db = get_db()
    return list(db.books.find({"genre": genre}))


def get_books_by_language(language):
    """Get books by language"""
    db = get_db()
    return list(db.books.find({"language": language}))


def search_books(query):
    """Search books by title or author"""
    db = get_db()
    return list(db.books.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"author": {"$regex": query, "$options": "i"}}
        ]
    }))


def get_available_books():
    """Get only available books"""
    db = get_db()
    return list(db.books.find({"available": True}))


# ---------- UPDATE ----------
def update_book(book_id, update_data):
    """Update book information"""
    db = get_db()
    try:
        update_data["updated_at"] = datetime.utcnow()
        result = db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


def toggle_book_availability(book_id, available):
    """Toggle book availability"""
    return update_book(book_id, {"available": available})


# ---------- DELETE ----------
def delete_book(book_id):
    """Delete a book"""
    db = get_db()
    try:
        result = db.books.delete_one({"_id": ObjectId(book_id)})
        return result.deleted_count > 0
    except:
        return False