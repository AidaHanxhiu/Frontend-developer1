# This file contains all database operations for books
# It provides functions to create, read, update, and delete books in MongoDB
# The frontend calls these functions through the API routes

from bson import ObjectId
from datetime import datetime


# Database connection helper function
# This function establishes a connection to MongoDB using the connection string from .env file
# All model functions use this to get the database connection
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
# Function to create a new book in the database
# This is called when an admin adds a new book through the admin panel
# The 'available' field defaults to True, meaning new books start as available for borrowing
def create_book(data):
    """Create a new book"""
    db = get_db()
    
    # Build the book document with all required fields
    # The 'available' field is critical: it determines if the book shows as "Available" or "Borrowed" in the UI
    # When a book is first created, available=True means it can be borrowed immediately
    book = {
        "title": data.get("title", ""),
        "author": data.get("author", ""),
        "year": data.get("year"),
        "isbn": data.get("isbn", ""),
        "description": data.get("description", ""),
        "genre": data.get("genre", ""),
        "language": data.get("language", "English"),
        # THE 'available' FIELD IS THE SOURCE OF TRUTH FOR BOOK STATUS
        # True = book is available for borrowing (shows "Available" badge in UI)
        # False = book is currently borrowed (shows "Borrowed" badge in UI)
        # This field is updated when books are borrowed (set to False) and returned (set to True)
        "available": data.get("available", True),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert the book document into the MongoDB 'books' collection
    result = db.books.insert_one(book)
    book["_id"] = result.inserted_id
    return book


# ---------- READ ----------
# Function to get all books from the database
# Used by the "All Books" page to display the complete catalog
# Returns all books regardless of availability status
def get_all_books():
    """Get all books"""
    db = get_db()
    return list(db.books.find({}))


# Function to get a single book by its ID
# Used when viewing book details or when borrowing a specific book
# The book_id comes from the URL (e.g., /book/12345)
def get_book_by_id(book_id):
    """Get book by ID"""
    db = get_db()
    try:
        return db.books.find_one({"_id": ObjectId(book_id)})
    except:
        return None


# Function to filter books by genre
# Used by the "All Genres" page to show books in a specific category
# Example: get all "Fantasy" books
def get_books_by_genre(genre):
    """Get books by genre"""
    db = get_db()
    return list(db.books.find({"genre": genre}))


# Function to filter books by language
# Used by the "All Languages" page to show books in a specific language
# Example: get all "Spanish" books
def get_books_by_language(language):
    """Get books by language"""
    db = get_db()
    return list(db.books.find({"language": language}))


# Function to search books by title or author name
# Used by the Search page when users type in the search box
# The search is case-insensitive (i option) and matches partial text
# Example: searching "harry" will find "Harry Potter"
def search_books(query):
    """Search books by title or author"""
    db = get_db()
    return list(db.books.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"author": {"$regex": query, "$options": "i"}}
        ]
    }))


# Function to get only books that are currently available for borrowing
# Used by the "Available Only" filter on the All Books page
# Only returns books where available=True
# This helps users find books they can actually borrow right now
def get_available_books():
    """Get only available books"""
    db = get_db()
    return list(db.books.find({"available": True}))


# ---------- UPDATE ----------
# Function to update any field of a book
# This is a general-purpose update function used for:
# - Updating book availability when borrowing/returning (available=True/False)
# - Updating book details in the admin panel (title, author, etc.)
# The update_data dictionary contains the fields to change
# Example: update_book("123", {"available": False}) marks the book as borrowed
def update_book(book_id, update_data):
    """Update book information"""
    db = get_db()
    try:
        # Always update the updated_at timestamp when any field changes
        update_data["updated_at"] = datetime.utcnow()
        # Update the book document in MongoDB
        # $set operator updates only the specified fields, leaving others unchanged
        result = db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": update_data}
        )
        # Return True if the update succeeded (at least one document was modified)
        return result.modified_count > 0
    except:
        return False


# Helper function specifically for changing book availability
# This is a convenience function that wraps update_book()
# Used when borrowing (set available=False) or returning (set available=True)
# The availability change is what makes the book show as "Available" or "Borrowed" in the UI
def toggle_book_availability(book_id, available):
    """Toggle book availability"""
    return update_book(book_id, {"available": available})


# ---------- DELETE ----------
# Function to permanently delete a book from the database
# Used by admins to remove books from the catalog
# WARNING: This is permanent and cannot be undone
def delete_book(book_id):
    """Delete a book"""
    db = get_db()
    try:
        result = db.books.delete_one({"_id": ObjectId(book_id)})
        return result.deleted_count > 0
    except:
        return False