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
def create_review(user_id, book_id, rating, comment=None):
    """Create a new review"""
    db = get_db()
    
    # Check if user already reviewed this book
    existing = db.reviews.find_one({
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id)
    })
    
    if existing:
        # Update existing review
        return update_review(existing["_id"], rating, comment)
    
    review = {
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id),
        "rating": rating,
        "comment": comment,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = db.reviews.insert_one(review)
    review["_id"] = result.inserted_id
    return review


# ---------- READ ----------
def get_book_reviews(book_id):
    """Get all reviews for a book"""
    db = get_db()
    try:
        return list(db.reviews.find({"book_id": ObjectId(book_id)}))
    except:
        return []


def get_user_reviews(user_id):
    """Get all reviews by a user"""
    db = get_db()
    try:
        return list(db.reviews.find({"user_id": ObjectId(user_id)}))
    except:
        return []


def get_book_rating(book_id):
    """Get average rating for a book"""
    db = get_db()
    try:
        reviews = get_book_reviews(book_id)
        if not reviews:
            return 0
        total = sum(r["rating"] for r in reviews)
        return round(total / len(reviews), 1)
    except:
        return 0


# ---------- UPDATE ----------
def update_review(review_id, rating=None, comment=None):
    """Update a review"""
    db = get_db()
    try:
        update_data = {"updated_at": datetime.utcnow()}
        if rating is not None:
            update_data["rating"] = rating
        if comment is not None:
            update_data["comment"] = comment
        
        result = db.reviews.update_one(
            {"_id": ObjectId(review_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


# ---------- DELETE ----------
def delete_review(review_id):
    """Delete a review"""
    db = get_db()
    try:
        result = db.reviews.delete_one({"_id": ObjectId(review_id)})
        return result.deleted_count > 0
    except:
        return False

