from bson import ObjectId
from datetime import datetime, timedelta


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
def create_loan(user_id, book_id, due_days=14):
    """Create a new loan"""
    db = get_db()
    
    loan = {
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id),
        "borrowed_date": datetime.utcnow(),
        "due_date": datetime.utcnow() + timedelta(days=due_days),
        "returned_date": None,
        "status": "active"
    }
    
    result = db.loans.insert_one(loan)
    loan["_id"] = result.inserted_id
    return loan


# ---------- READ ----------
def get_all_loans():
    """Get all loans"""
    db = get_db()
    return list(db.loans.find({}))


def get_loan_by_id(loan_id):
    """Get loan by ID"""
    db = get_db()
    try:
        return db.loans.find_one({"_id": ObjectId(loan_id)})
    except:
        return None


def get_user_loans(user_id):
    """Get all loans for a user, joined with book details using $lookup"""
    db = get_db()
    try:
        pipeline = [
            {"$match": {"user_id": ObjectId(user_id)}},
            {
                "$lookup": {
                    "from": "books",
                    "localField": "book_id",
                    "foreignField": "_id",
                    "as": "book"
                }
            },
            {
                "$unwind": {
                    "path": "$book",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]
        return list(db.loans.aggregate(pipeline))
    except:
        return []


def get_active_loans(user_id):
    """Get active loans for a user, joined with book details using $lookup"""
    db = get_db()
    try:
        pipeline = [
            {"$match": {
                "user_id": ObjectId(user_id),
                "status": "active"
            }},
            {
                "$lookup": {
                    "from": "books",
                    "localField": "book_id",
                    "foreignField": "_id",
                    "as": "book"
                }
            },
            {
                "$unwind": {
                    "path": "$book",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]
        return list(db.loans.aggregate(pipeline))
    except:
        return []


def get_book_loans(book_id):
    """Get all loans for a book"""
    db = get_db()
    try:
        return list(db.loans.find({"book_id": ObjectId(book_id)}))
    except:
        return []


# ---------- UPDATE ----------
def return_loan(loan_id):
    """Mark a loan as returned"""
    db = get_db()
    try:
        result = db.loans.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    "returned_date": datetime.utcnow(),
                    "status": "returned"
                }
            }
        )
        return result.modified_count > 0
    except:
        return False


# ---------- DELETE ----------
def delete_loan(loan_id):
    """Delete a loan"""
    db = get_db()
    try:
        result = db.loans.delete_one({"_id": ObjectId(loan_id)})
        return result.deleted_count > 0
    except:
        return False


# ---------- RESERVATIONS (NEW CLASS) ----------
# TODO: adjust fields (status workflow, dates) as needed.
def create_reservation(user_id, book_id, status="pending"):
    """Create a new reservation"""
    db = get_db()

    reservation = {
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id),
        "reserved_date": datetime.utcnow(),
        "status": status
    }

    result = db.reservations.insert_one(reservation)
    reservation["_id"] = result.inserted_id
    return reservation


def get_all_reservations():
    """Get all reservations"""
    db = get_db()
    return list(db.reservations.find({}))


def get_reservation_by_id(reservation_id):
    """Get reservation by ID"""
    db = get_db()
    try:
        return db.reservations.find_one({"_id": ObjectId(reservation_id)})
    except:
        return None


def get_user_reservations(user_id):
    """Get all reservations for a user"""
    db = get_db()
    try:
        return list(db.reservations.find({"user_id": ObjectId(user_id)}))
    except:
        return []


def update_reservation(reservation_id, update_data):
    """Update reservation information"""
    db = get_db()
    try:
        result = db.reservations.update_one(
            {"_id": ObjectId(reservation_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except:
        return False


def delete_reservation(reservation_id):
    """Delete a reservation"""
    db = get_db()
    try:
        result = db.reservations.delete_one({"_id": ObjectId(reservation_id)})
        return result.deleted_count > 0
    except:
        return False