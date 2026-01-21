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
# Function to create a new loan record when a user borrows a book
# A loan represents the relationship between a user and a book they borrowed
# This function is called by the backend API when a user clicks "Confirm Borrow"
# 
# IMPORTANT: Creating a loan does NOT automatically update the book's availability
# The API route must also call update_book() to set available=False
# This ensures both the loan record AND book status are updated together
def create_loan(user_id, book_id, due_days=14):
    """Create a new loan"""
    db = get_db()
    
    # Build the loan document with all required fields
    # A loan connects a user to a book and tracks the borrowing period
    loan = {
        # user_id: Which user borrowed the book (links to users collection)
        "user_id": ObjectId(user_id),
        # book_id: Which book was borrowed (links to books collection)
        # This is critical - we need this ID to update the book's availability when returning
        "book_id": ObjectId(book_id),
        # borrowed_date: When the loan started (today)
        "borrowed_date": datetime.utcnow(),
        # due_date: When the book must be returned (default 14 days from now)
        # Used to check if a loan is overdue
        "due_date": datetime.utcnow() + timedelta(days=due_days),
        # returned_date: Initially None, set to current date when book is returned
        # None means the book is still borrowed
        "returned_date": None,
        # status: "active" means book is currently borrowed, "returned" means it was returned
        # Used to filter active vs completed loans
        "status": "active"
    }
    
    # Insert the loan document into the MongoDB 'loans' collection
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


# Function to get all loans for a specific user, including book details
# Used by the "My Books" and "My Loans" pages to show what the user has borrowed
# 
# WHY WE USE $lookup (JOIN):
# - Loans collection only stores book_id (a reference)
# - To display book title and author, we need to join with the books collection
# - $lookup performs a join: for each loan, find the matching book document
# - $unwind converts the joined book array into a single book object
# 
# RESULT: Each loan object includes a nested "book" object with title, author, etc.
# This allows the frontend to display "Harry Potter" instead of just a book ID
def get_user_loans(user_id):
    """Get all loans for a user, joined with book details using $lookup"""
    db = get_db()
    try:
        # MongoDB aggregation pipeline: a series of operations on the data
        pipeline = [
            # Step 1: Filter to only loans for this user
            {"$match": {"user_id": ObjectId(user_id)}},
            # Step 2: Join with books collection to get book details
            # This is like a SQL JOIN: match loan.book_id with book._id
            {
                "$lookup": {
                    "from": "books",              # Collection to join with
                    "localField": "book_id",      # Field in loans collection
                    "foreignField": "_id",        # Field in books collection
                    "as": "book"                  # Name of the joined field
                }
            },
            # Step 3: Convert the book array into a single book object
            # $lookup returns an array, but we want a single object
            {
                "$unwind": {
                    "path": "$book",
                    "preserveNullAndEmptyArrays": True  # Keep loan even if book not found
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
# Function to mark a loan as returned
# This updates the loan record but does NOT update the book's availability
# 
# IMPORTANT: The API route must also call update_book() to set available=True
# This function only updates the loan status - it's part of a two-step process:
# 1. Update loan: set status="returned" and returned_date=now (this function)
# 2. Update book: set available=True (done by the API route)
# 
# WHY BOTH UPDATES ARE NEEDED:
# - Loan update: Preserves borrowing history (who borrowed what, when returned)
# - Book update: Makes the book show as "Available" in the UI
# Without the book update, All Books page would still show "Borrowed"
def return_loan(loan_id):
    """Mark a loan as returned"""
    db = get_db()
    try:
        # Update the loan document to mark it as returned
        # This preserves the borrowing history in the database
        result = db.loans.update_one(
            {"_id": ObjectId(loan_id)},
            {
                "$set": {
                    # Set the return date to now (when the book was returned)
                    "returned_date": datetime.utcnow(),
                    # Change status from "active" to "returned"
                    # This allows filtering active vs completed loans
                    "status": "returned"
                }
            }
        )
        # Return True if the update succeeded
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