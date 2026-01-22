"""
API Routes Module - routes/routes_api.py

This module contains all API endpoints for the Library System application.
API endpoints return JSON data (not HTML pages) and are used by:
- Frontend JavaScript (AJAX/fetch requests)
- Mobile apps (if any)
- External clients

API endpoints are prefixed with /api (e.g., /api/books, /api/loans)

Main sections:
- Authentication: /api/login, /api/signup
- Books: /api/books (GET with filtering)
- Loans: /api/loans (GET, POST), /api/loans/<id>/return (POST)
- Wishlist: (if implemented)
- Reviews: (if implemented)

All endpoints use JSON for request/response and handle errors gracefully.
"""

# ---------- IMPORTS ----------
# Standard library imports
import logging                     # Used for logging errors and debug info
import sys                         # Used to flush stdout for console printing

# Flask-related imports
from flask import Blueprint, jsonify, request, session, current_app

# JWT authentication utilities
from flask_jwt_extended import (
    create_access_token,          # Create JWT access tokens
    jwt_required,                 # Protect routes with JWT (not always used)
    get_jwt_identity,             # Get user ID from JWT
    verify_jwt_in_request         # Verify JWT optionally
)

# MongoDB ObjectId handling
from bson import ObjectId
from bson.json_util import dumps  # Convert BSON to JSON

# ---------- MODEL IMPORTS ----------
# User-related database operations
from models.users_model import (
    verify_user,                  # Verify email/password
    get_user_by_email,            # Fetch user by email
    create_user,                  # Create new user
    get_all_users,                # Fetch all users
    update_user,                  # Update user info
    delete_user,                  # Delete user
    create_password_reset_token,  # Create password reset token
    verify_reset_token,           # Validate reset token
    invalidate_reset_token,       # Mark token as used
    update_user_password          # Update hashed password
)

# Book-related database operations
from models.books_model import (
    get_all_books,                # Fetch all books
    get_book_by_id,               # Fetch book by ID
    create_book,                  # Create book
    update_book,                  # Update book
    delete_book,                  # Delete book
    search_books,                 # Search by title/author
    get_available_books,          # Fetch available books
    get_books_by_genre,           # Fetch by genre
    get_books_by_language,        # Fetch by language
    toggle_book_availability      # Toggle book availability
)

# Loan and reservation operations
from models.loans_model import (
    create_loan,                  # Create loan
    get_user_loans,               # Fetch user's loans
    get_active_loans,             # Fetch active loans
    get_loan_by_id,               # Fetch loan by ID
    return_loan,                  # Mark loan returned
    delete_loan,                  # Delete loan
    create_reservation,           # Create reservation
    get_all_reservations,         # Fetch all reservations
    get_reservation_by_id,        # Fetch reservation by ID
    get_user_reservations,        # Fetch user's reservations
    update_reservation,           # Update reservation
    delete_reservation,           # Delete reservation
)

# Requests, wishlist, reviews, genres, authors
from models.requests_model import (
    create_request,               # Create request
    get_user_requests,            # Fetch user requests
    get_all_requests,             # Fetch all requests
    update_request_status,        # Update request status
    delete_request                # Delete request
)

from models.wishlist_model import (
    add_to_wishlist,              # Add book to wishlist
    get_user_wishlist,            # Fetch wishlist
    remove_from_wishlist,         # Remove wishlist item
    is_in_wishlist                # Check wishlist status
)

from models.reviews_model import (
    create_review,                # Create/update review
    get_all_reviews,              # Fetch all reviews
    get_review_by_id,             # Fetch review
    get_book_reviews,             # Fetch book reviews
    get_book_rating,              # Calculate rating
    update_review,                # Update review
    delete_review,                # Delete review
)

from models.genres_model import (
    get_all_genres,               # Fetch genres
    create_genre                  # Create genre
)

from models.authors_model import (
    get_all_authors,              # Fetch authors
    create_publisher,             # Create publisher
    get_all_publishers,           # Fetch publishers
    get_publisher_by_id,          # Fetch publisher
    update_publisher,             # Update publisher
    delete_publisher,             # Delete publisher
)

# ---------- API BLUEPRINT ----------
# Create API blueprint with /api prefix
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Enable debug-level logging
logging.basicConfig(level=logging.DEBUG)

# ---------- HELPER FUNCTIONS ----------

def serialize_doc(doc):
    """
    Convert MongoDB documents (ObjectId) into JSON-serializable format
    
    MongoDB uses ObjectId for document IDs, but JSON doesn't support ObjectId.
    This function recursively converts all ObjectIds to strings so the data
    can be sent to the frontend as JSON.
    
    Args:
        doc: MongoDB document (dict), list of documents, or primitive value
        
    Returns:
        Same structure with ObjectIds converted to strings
    """
    # Handle None/null values
    if doc is None:
        return None                          # Return None if document is empty

    # Handle lists - recursively serialize each item
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]  # Recursively serialize lists

    # Handle dictionaries - convert ObjectIds and recurse into nested structures
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            # MongoDB ObjectIds need to be converted to strings for JSON
            if isinstance(value, ObjectId):
                result[key] = str(value)     # Convert ObjectId to string
            # Nested lists or dicts need recursive processing
            elif isinstance(value, (list, dict)):
                result[key] = serialize_doc(value)  # Recursive conversion
            # Primitive values (strings, numbers, booleans) can be used as-is
            else:
                result[key] = value
        return result

    # Primitive values (strings, numbers, booleans) don't need conversion
    return doc                               # Return primitive values unchanged


def get_current_user_id():
    """
    Retrieve user ID from JWT token if available,
    otherwise fall back to session-based authentication.
    
    This function supports both authentication methods:
    1. JWT tokens (for API calls from mobile apps or external clients)
    2. Flask sessions (for web browser requests)
    
    Returns:
        str: User ID if authenticated, None otherwise
    """
    try:
        # Try to get user ID from JWT token first (for API authentication)
        verify_jwt_in_request(optional=True)  # Check JWT if present (doesn't fail if missing)
        user_id = get_jwt_identity()          # Get user ID from token
        if user_id:
            return user_id                    # Return JWT user ID if found
    except Exception as e:
        # JWT verification failed, but that's OK - we'll try session instead
        logging.debug(f"JWT verification failed: {str(e)}")  # Log JWT errors for debugging

    # Fall back to Flask session (for web browser requests)
    return session.get("user_id")             # Fallback to session-based auth


def get_current_user_role():
    """
    Retrieve user role from session
    """
    return session.get("user_role")           # Used for admin checks

# ---------- AUTHENTICATION ROUTES ----------

@api_bp.route("/login", methods=["POST"])
def login():
    """
    User login endpoint with JWT token generation
    
    This endpoint:
    1. Receives email and password from the frontend
    2. Validates credentials against the database
    3. Creates a JWT token for API authentication
    4. Stores user info in Flask session for web requests
    5. Returns token and user info to the frontend
    
    Request body (JSON):
        {
            "email": "user@example.com",
            "password": "password123"
        }
    
    Returns:
        Success (200): {message, access_token, role, user_id}
        Error (400): {message: "Invalid credentials"}
    """
    try:
        # Extract login credentials from request
        data = request.get_json() or {}        # Read JSON body (empty dict if None)
        email = data.get("email")              # Extract email from request
        password = data.get("password")        # Extract password from request

        # Validate that both email and password were provided
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        # Verify credentials against database (checks email exists and password matches)
        user = verify_user(email, password)    # Validate credentials, returns user dict or None

        # If credentials are valid, create authentication tokens
        if user:
            # Create JWT token for API authentication (used by mobile apps or external clients)
            access_token = create_access_token(identity=str(user["_id"]))

            # Store session data for backward compatibility (used by web browser requests)
            # Flask sessions allow the web app to remember the logged-in user
            session.permanent = True           # Make session persist across browser restarts
            session["user_id"] = str(user["_id"])      # Store user ID in session
            session["user_email"] = user["email"]      # Store email in session
            session["user_role"] = user["role"]        # Store role (admin/student) in session

            # Return success response with token and user info
            return jsonify({
                "message": "Login successful",
                "access_token": access_token,  # JWT token for API calls
                "role": user["role"],          # User role (admin or student)
                "user_id": str(user["_id"])    # User ID as string
            })

        # Credentials were invalid
        return jsonify({"message": "Invalid credentials"}), 400

    except Exception as e:
        # Log error for debugging (don't expose internal errors to users)
        logging.error(f"Login error: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/signup", methods=["POST"])
def signup():
    """
    User registration endpoint - Creates a new user account
    
    This endpoint:
    1. Validates user input (name, email, password)
    2. Checks if email already exists
    3. Creates new user account with hashed password
    4. Returns success or error message
    
    Request body (JSON):
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "password123"
        }
    
    Returns:
        Success (201): {message, success: true}
        Error (400): {message: "Email already exists" or validation error}
    """
    try:
        # Extract user registration data from request
        data = request.get_json() or {}        # Get JSON body
        first_name = data.get("first_name", "").strip()    # Get first name, remove whitespace
        last_name = data.get("last_name", "").strip()      # Get last name, remove whitespace
        email = data.get("email", "").strip()              # Get email, remove whitespace
        password = data.get("password", "")                 # Get password (don't strip, spaces might be intentional)

        # Validate required fields - ensure all required data is provided
        if not first_name or not last_name:
            return jsonify({"message": "First name and last name are required"}), 400

        if not email:
            return jsonify({"message": "Email is required"}), 400

        # Validate password strength (minimum 6 characters)
        if not password or len(password) < 6:
            return jsonify({"message": "Password must be at least 6 characters"}), 400

        # Create user account in database
        # This function hashes the password and stores user info
        # Returns user dict if successful, None if email already exists
        user = create_user(first_name, last_name, email, password)

        # Check if user was created successfully
        if user:
            # User created successfully
            return jsonify({
                "message": "Account created successfully!",
                "success": True
            }), 201  # 201 = Created
        else:
            # Email already exists in database
            return jsonify({"message": "Email already exists"}), 400

    except Exception as e:
        # Log error for debugging
        logging.error(f"Signup error: {str(e)}")
        return jsonify({"message": "Server error"}), 500

# ---------- BOOK ROUTES ----------

@api_bp.route("/books", methods=["GET"])
def get_books():
    """
    Get all books with optional filtering
    
    This endpoint supports multiple query parameters for filtering books:
    - available=true: Only show available books
    - search=query: Search by title or author
    - genre=name: Filter by genre
    - language=name: Filter by language
    
    Example requests:
        GET /api/books                          # All books
        GET /api/books?available=true           # Only available books
        GET /api/books?search=harry             # Search for "harry"
        GET /api/books?genre=Fantasy           # Fantasy books only
        GET /api/books?available=true&genre=Fiction  # Available fiction books
    
    Returns:
        Success (200): {books: [...]}
        Error (500): {message, books: []}
    """
    try:
        # Extract query parameters from URL (e.g., ?available=true&search=harry)
        available_only = request.args.get("available", "").lower() == "true"  # Convert "true" string to boolean
        search_query = request.args.get("search", "").strip()                  # Get search term, remove whitespace
        genre_filter = request.args.get("genre", "").strip()                   # Get genre filter
        language_filter = request.args.get("language", "").strip()             # Get language filter

        # Step 1: Get base list of books (all books or only available ones)
        if available_only:
            # Only fetch books that are currently available for borrowing
            books = get_available_books()  # Returns books where available=True
        else:
            # Fetch all books regardless of availability status
            books = get_all_books()       # Returns all books in database

        # Step 2: Apply search filter (if provided)
        # Search checks both title and author fields (case-insensitive)
        if search_query:
            # Filter books by title or author (case-insensitive matching)
            books = [b for b in books if 
                    search_query.lower() in b.get("title", "").lower() or      # Check if search term is in title
                    search_query.lower() in b.get("author", "").lower()]      # Check if search term is in author

        # Step 3: Apply genre filter (if provided)
        if genre_filter:
            # Keep only books that match the specified genre
            books = [b for b in books if b.get("genre") == genre_filter]

        # Step 4: Apply language filter (if provided)
        if language_filter:
            # Keep only books in the specified language
            books = [b for b in books if b.get("language") == language_filter]

        # Step 5: Convert MongoDB ObjectIds to strings for JSON response
        # This is necessary because JSON doesn't support MongoDB ObjectId type
        serialized_books = serialize_doc(books)

        # Return filtered books as JSON
        return jsonify({"books": serialized_books})

    except Exception as e:
        # Log error and return empty list (don't crash the frontend)
        logging.error(f"Error fetching books: {str(e)}")
        return jsonify({"message": "Error fetching books", "books": []}), 500

# ---------- LOAN ROUTES ----------

@api_bp.route("/loans", methods=["GET"])
def get_user_loans_endpoint():
    """
    Get all loans for the current logged-in user
    
    This endpoint:
    1. Gets the current user ID from session/JWT
    2. Fetches all loans for that user (both active and returned)
    3. Includes book details for each loan (title, author, etc.)
    4. Returns loans as JSON
    
    Returns:
        Success (200): {loans: [{loan data with book info}, ...]}
        Error (401): {message: "Authentication required", loans: []}
        Error (500): {message: "Error fetching loans", loans: []}
    """
    try:
        # Step 1: Get the current user's ID (from session or JWT token)
        user_id = get_current_user_id()
        if not user_id:
            # User is not logged in
            return jsonify({"message": "Authentication required", "loans": []}), 401

        # Log for debugging (helps track down issues)
        logging.debug(f"Fetching loans for user_id: {user_id} (type: {type(user_id)})")

        # Step 2: Fetch user's loans from database
        # This function uses MongoDB $lookup to join loans with books collection
        # So each loan includes full book details (title, author, etc.)
        loans = get_user_loans(user_id)
        
        # Log how many loans were found (for debugging)
        logging.debug(f"Found {len(loans)} loans for user")
        
        # Step 3: Convert MongoDB ObjectIds to strings for JSON response
        # Loans contain ObjectIds for user_id, book_id, _id - these need to be strings
        serialized_loans = serialize_doc(loans)

        # Return loans as JSON array
        return jsonify({"loans": serialized_loans})

    except Exception as e:
        # Log full error details for debugging
        logging.error(f"Error fetching loans: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())  # Print full stack trace
        return jsonify({"message": "Error fetching loans", "loans": []}), 500


@api_bp.route("/loans", methods=["POST"])
def borrow_book():
    """
    Create a new loan (borrow a book)
    
    This endpoint:
    1. Validates user is logged in
    2. Checks book exists and is available
    3. Creates loan record in database
    4. Updates book availability to False (marks as borrowed)
    5. Returns loan details
    
    Request body (JSON):
        {
            "book_id": "507f1f77bcf86cd799439011"
        }
    
    Returns:
        Success (201): {message: "Book borrowed successfully", loan: {...}}
        Error (400): {message: "Book is not available"}
        Error (401): {message: "Authentication required"}
        Error (404): {message: "Book not found"}
    """
    try:
        # Step 1: Verify user is logged in
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required"}), 401

        # Step 2: Extract book_id from request body
        data = request.get_json() or {}        # Get JSON body
        book_id = data.get("book_id")          # Extract book_id

        # Validate book_id was provided
        if not book_id:
            return jsonify({"message": "book_id is required"}), 400

        # Step 3: Verify book exists in database
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404

        # Step 4: Check if book is available for borrowing
        # If book.available is False, someone else already borrowed it
        if not book.get("available"):
            return jsonify({"message": "Book is not available"}), 400

        # Step 5: Create loan record in database
        # This creates a new document in the loans collection with:
        # - user_id: who borrowed it
        # - book_id: which book
        # - borrowed_date: when it was borrowed
        # - due_date: when it should be returned (14 days from now)
        # - status: "active"
        loan = create_loan(user_id, book_id)
        
        # Step 6: Update book availability to False
        # This marks the book as "borrowed" so others can't borrow it
        # Important: This must happen AFTER creating the loan
        toggle_book_availability(book_id, False)

        # Step 7: Convert ObjectIds to strings for JSON response
        serialized_loan = serialize_doc(loan)

        # Return success response with loan details
        return jsonify({
            "message": "Book borrowed successfully",
            "loan": serialized_loan
        }), 201  # 201 = Created

    except Exception as e:
        # Log error with full stack trace for debugging
        logging.error(f"Error creating loan: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"message": "Error borrowing book"}), 500


@api_bp.route("/loans/<loan_id>/return", methods=["POST"])
def return_book(loan_id):
    """
    Return a book (mark loan as returned)
    
    This endpoint:
    1. Verifies user is logged in
    2. Verifies loan exists and belongs to current user
    3. Checks loan hasn't already been returned
    4. Updates loan status to "returned"
    5. Updates book availability to True (makes it available again)
    
    URL parameter:
        loan_id: The ID of the loan to return
    
    Returns:
        Success (200): {message: "Book returned successfully"}
        Error (400): {message: "Book already returned"}
        Error (401): {message: "Authentication required"}
        Error (403): {message: "Unauthorized"} (loan doesn't belong to user)
        Error (404): {message: "Loan not found"}
    """
    try:
        # Step 1: Verify user is logged in
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required"}), 401

        # Step 2: Fetch loan from database to verify it exists
        # We need the loan to:
        # - Check if it exists
        # - Verify it belongs to the current user
        # - Get the book_id to update book availability
        loan = get_loan_by_id(loan_id)
        
        if not loan:
            return jsonify({"message": "Loan not found"}), 404

        # Step 3: Security check - verify the loan belongs to the current user
        # This prevents users from returning other people's loans
        if str(loan.get("user_id")) != str(user_id):
            return jsonify({"message": "Unauthorized"}), 403  # 403 = Forbidden

        # Step 4: Check if book was already returned
        # Prevents duplicate returns
        if loan.get("status") == "returned":
            return jsonify({"message": "Book already returned"}), 400

        # Step 5: Update loan status to "returned"
        # This sets:
        # - status: "returned"
        # - returned_date: current timestamp
        return_loan(loan_id)

        # Step 6: Update book availability to True
        # This makes the book available for others to borrow again
        # Important: Must happen AFTER updating loan status
        book_id = loan.get("book_id")
        if book_id:
            # Convert ObjectId to string (book_id might be ObjectId type)
            book_id_str = str(book_id)
            toggle_book_availability(book_id_str, True)  # Set available=True

        # Return success message
        return jsonify({"message": "Book returned successfully"})

    except Exception as e:
        # Log error for debugging
        logging.error(f"Error returning book: {str(e)}")
        return jsonify({"message": "Error returning book"}), 500

# ---------- WISHLIST ROUTES ----------

@api_bp.route("/wishlist", methods=["GET"])
def get_wishlist():
    """
    Get user's wishlist with book details
    
    This endpoint:
    1. Gets the current user ID from session/JWT
    2. Fetches all wishlist items for that user
    3. Returns wishlist items as JSON
    
    Returns:
        Success (200): {wishlist: [{wishlist_item}, ...]}
        Error (401): {message: "Authentication required", wishlist: []}
        Error (500): {message: "Error fetching wishlist", wishlist: []}
    """
    try:
        # Step 1: Get the current user's ID (from session or JWT token)
        user_id = get_current_user_id()
        if not user_id:
            # User is not logged in
            return jsonify({"message": "Authentication required", "wishlist": []}), 401

        # Step 2: Fetch user's wishlist from database
        # This returns a list of wishlist items, each containing book_id
        wishlist_items = get_user_wishlist(user_id)
        
        # Step 3: Convert MongoDB ObjectIds to strings for JSON response
        # Wishlist items contain ObjectIds for user_id, book_id, _id - these need to be strings
        serialized_wishlist = serialize_doc(wishlist_items)

        # Return wishlist as JSON array
        return jsonify({"wishlist": serialized_wishlist})

    except Exception as e:
        # Log error for debugging
        logging.error(f"Error fetching wishlist: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"message": "Error fetching wishlist", "wishlist": []}), 500


@api_bp.route("/wishlist", methods=["POST"])
def add_to_wishlist_endpoint():
    """
    Add a book to user's wishlist
    
    This endpoint:
    1. Validates user is logged in
    2. Checks book exists
    3. Adds book to user's wishlist (if not already there)
    4. Returns success message
    
    Request body (JSON):
        {
            "book_id": "507f1f77bcf86cd799439011"
        }
    
    Returns:
        Success (201): {message: "Book added to wishlist", wishlist_item: {...}}
        Error (400): {message: "book_id is required"}
        Error (401): {message: "Authentication required"}
        Error (404): {message: "Book not found"}
    """
    try:
        # Step 1: Verify user is logged in
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required"}), 401

        # Step 2: Extract book_id from request body
        data = request.get_json() or {}        # Get JSON body
        book_id = data.get("book_id")          # Extract book_id

        # Validate book_id was provided
        if not book_id:
            return jsonify({"message": "book_id is required"}), 400

        # Step 3: Verify book exists in database
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404

        # Step 4: Add book to wishlist
        # This function checks if already in wishlist and returns existing item if so
        wishlist_item = add_to_wishlist(user_id, book_id)
        
        # Step 5: Convert ObjectIds to strings for JSON response
        serialized_item = serialize_doc(wishlist_item)

        # Return success response with wishlist item
        return jsonify({
            "message": "Book added to wishlist",
            "wishlist_item": serialized_item
        }), 201  # 201 = Created

    except Exception as e:
        # Log error with full stack trace for debugging
        logging.error(f"Error adding to wishlist: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"message": "Error adding to wishlist"}), 500


@api_bp.route("/wishlist/<book_id>", methods=["DELETE"])
def remove_from_wishlist_endpoint(book_id):
    """
    Remove a book from user's wishlist
    
    This endpoint:
    1. Validates user is logged in
    2. Removes book from user's wishlist
    3. Returns success message
    
    URL parameter:
        book_id: The ID of the book to remove from wishlist
    
    Returns:
        Success (200): {message: "Book removed from wishlist"}
        Error (400): {message: "book_id is required"}
        Error (401): {message: "Authentication required"}
        Error (404): {message: "Book not found in wishlist"}
    """
    try:
        # Step 1: Verify user is logged in
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required"}), 401

        # Validate book_id was provided
        if not book_id:
            return jsonify({"message": "book_id is required"}), 400

        # Step 2: Remove book from wishlist
        # This function returns True if book was removed, False if not found
        success = remove_from_wishlist(user_id, book_id)

        if success:
            # Book was successfully removed
            return jsonify({"message": "Book removed from wishlist"})
        else:
            # Book was not found in wishlist
            return jsonify({"message": "Book not found in wishlist"}), 404

    except Exception as e:
        # Log error for debugging
        logging.error(f"Error removing from wishlist: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"message": "Error removing from wishlist"}), 500


@api_bp.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    """
    Get a single book by ID
    
    This endpoint is used by the wishlist page to fetch book details
    for each wishlist item.
    
    URL parameter:
        book_id: The ID of the book to fetch
    
    Returns:
        Success (200): {book data as JSON}
        Error (404): {message: "Book not found"}
        Error (500): {message: "Error fetching book"}
    """
    try:
        # Fetch book from database
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404

        # Convert MongoDB ObjectIds to strings for JSON response
        serialized_book = serialize_doc(book)

        # Return book as JSON
        return jsonify(serialized_book)

    except Exception as e:
        # Log error for debugging
        logging.error(f"Error fetching book: {str(e)}")
        return jsonify({"message": "Error fetching book"}), 500
