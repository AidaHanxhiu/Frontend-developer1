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
    """
    Create a new loan record when a user borrows a book
    
    Args:
        user_id: The ID of the user borrowing the book (string or ObjectId)
        book_id: The ID of the book being borrowed (string or ObjectId)
        due_days: Number of days until the book is due (default: 14)
    
    Returns:
        dict: The created loan document with _id added
    
    Note:
        This function only creates the loan record. The API route must also
        update the book's availability to False separately.
    """
    db = get_db()
    
    # Convert string IDs to ObjectId if needed (MongoDB requires ObjectId type)
    # This handles cases where user_id/book_id come as strings from the API
    user_id_obj = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
    book_id_obj = ObjectId(book_id) if not isinstance(book_id, ObjectId) else book_id
    
    # Build the loan document with all required fields
    # A loan document represents the relationship between a user and a borrowed book
    loan = {
        # user_id: Which user borrowed the book (links to users collection)
        # This is a foreign key reference to the users collection
        "user_id": user_id_obj,
        
        # book_id: Which book was borrowed (links to books collection)
        # This is critical - we need this ID to update the book's availability when returning
        # This is a foreign key reference to the books collection
        "book_id": book_id_obj,
        
        # borrowed_date: When the loan started (today's date/time)
        # Used to track when the book was borrowed
        "borrowed_date": datetime.utcnow(),
        
        # due_date: When the book must be returned (default 14 days from now)
        # Calculated as: current time + due_days
        # Used to check if a loan is overdue (if current date > due_date and status="active")
        "due_date": datetime.utcnow() + timedelta(days=due_days),
        
        # returned_date: Initially None, set to current date when book is returned
        # None means the book is still borrowed (hasn't been returned yet)
        # When returned, this is set to the return date
        "returned_date": None,
        
        # status: "active" means book is currently borrowed, "returned" means it was returned
        # Used to filter active loans (currently borrowed) vs completed loans (returned)
        # Frontend uses this to show "Active" vs "Returned" badges
        "status": "active"
    }
    
    # Insert the loan document into the MongoDB 'loans' collection
    # MongoDB automatically generates a unique _id for the new document
    result = db.loans.insert_one(loan)
    
    # Add the generated _id to the loan dict so we can return it
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
    """
    Get all loans for a user, joined with book details using MongoDB $lookup
    
    This function uses MongoDB aggregation pipeline to:
    1. Filter loans for the specific user
    2. Join loans with books collection to get book details
    3. Return loans with embedded book information
    
    Args:
        user_id: The ID of the user (string or ObjectId)
    
    Returns:
        list: List of loan documents, each containing:
            - Loan fields (user_id, book_id, borrowed_date, due_date, status, etc.)
            - book: Nested object with book details (title, author, genre, etc.)
    
    Example return value:
        [
            {
                "_id": ObjectId("..."),
                "user_id": ObjectId("..."),
                "book_id": ObjectId("..."),
                "borrowed_date": datetime(...),
                "due_date": datetime(...),
                "status": "active",
                "book": {  # <-- This is added by $lookup
                    "_id": ObjectId("..."),
                    "title": "Harry Potter",
                    "author": "J.K. Rowling",
                    ...
                }
            },
            ...
        ]
    """
    db = get_db()
    try:
        # Convert user_id string to ObjectId if needed (MongoDB requires ObjectId for queries)
        user_id_obj = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
        
        # MongoDB aggregation pipeline: a series of operations on the data
        # Think of it like a series of filters and transformations
        pipeline = [
            # Step 1: Filter to only loans for this user
            # $match is like SQL WHERE clause - filters documents
            {"$match": {"user_id": user_id_obj}},
            
            # Step 2: Join with books collection to get book details
            # $lookup is like SQL LEFT JOIN: matches loan.book_id with book._id
            # This adds book information to each loan document
            {
                "$lookup": {
                    "from": "books",              # Collection to join with (the books table)
                    "localField": "book_id",      # Field in loans collection (loan.book_id)
                    "foreignField": "_id",        # Field in books collection (book._id)
                    "as": "book"                  # Name of the new field containing joined book data
                }
            },
            # After $lookup, each loan has: loan.book = [book_document]
            # The book field is an array (even if only one match)
            
            # Step 3: Convert the book array into a single book object
            # $unwind "unwraps" the array, turning [book] into book
            # This makes it easier to access: loan.book.title instead of loan.book[0].title
            {
                "$unwind": {
                    "path": "$book",                          # Field to unwrap
                    "preserveNullAndEmptyArrays": True        # Keep loan even if book not found
                    # preserveNullAndEmptyArrays=True means: if book doesn't exist,
                    # still include the loan (with book field as null)
                }
            }
            # After $unwind, each loan has: loan.book = book_document (not an array)
        ]
        
        # Execute the aggregation pipeline and convert result to list
        return list(db.loans.aggregate(pipeline))
    except Exception as e:
        # Log error for debugging (helps track down issues with user_id format, etc.)
        import logging
        logging.error(f"Error in get_user_loans: {str(e)}, user_id: {user_id}, type: {type(user_id)}")
        # Return empty list if anything goes wrong (prevents app crash)
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
    """
    Mark a loan as returned
    
    This function updates the loan document to indicate the book has been returned.
    It sets the returned_date and changes status from "active" to "returned".
    
    Args:
        loan_id: The ID of the loan to mark as returned (string or ObjectId)
    
    Returns:
        bool: True if loan was successfully updated, False otherwise
    
    Note:
        This function ONLY updates the loan record. The API route must also
        update the book's availability to True separately.
    
    What gets updated:
        - returned_date: Set to current timestamp
        - status: Changed from "active" to "returned"
    """
    db = get_db()
    try:
        # Update the loan document to mark it as returned
        # This preserves the borrowing history in the database
        # $set operator updates only the specified fields, leaving others unchanged
        result = db.loans.update_one(
            {"_id": ObjectId(loan_id)},  # Find loan by ID
            {
                "$set": {
                    # Set the return date to now (when the book was returned)
                    # This records when the book was actually returned
                    "returned_date": datetime.utcnow(),
                    
                    # Change status from "active" to "returned"
                    # This allows filtering active loans (currently borrowed) vs
                    # completed loans (returned) in the frontend
                    "status": "returned"
                }
            }
        )
        # Return True if the update succeeded (at least one document was modified)
        # modified_count > 0 means the loan was found and updated
        return result.modified_count > 0
    except:
        # If anything goes wrong (invalid loan_id, database error, etc.), return False
        # This prevents the app from crashing
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