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
# import logging: Python's built-in logging module
# Used to log errors, warnings, and debug messages to console/file
import logging

# import sys: Python's system-specific parameters module
# Used to flush stdout for console printing (ensures output appears immediately)
import sys

# Flask-related imports
# Blueprint: Groups related routes together (like a mini Flask app)
# jsonify: Converts Python dict to JSON HTTP response
# request: Access HTTP request data (body, headers, query params)
# session: Store user data across requests (like cookies)
# current_app: Access the Flask application instance
from flask import Blueprint, jsonify, request, session, current_app

# JWT authentication utilities
# JWT (JSON Web Tokens) are used for API authentication
# They allow clients to prove identity without sending password every time
from flask_jwt_extended import (
    create_access_token,          # Function to create JWT tokens (used after login)
    jwt_required,                 # Decorator to protect routes (require valid JWT)
    get_jwt_identity,             # Function to get user ID from JWT token
    verify_jwt_in_request         # Function to verify JWT token exists and is valid
)

# MongoDB ObjectId handling
# ObjectId: MongoDB's unique identifier type (not JSON-compatible)
# We need to convert ObjectIds to strings for JSON responses
from bson import ObjectId
# dumps: Convert MongoDB BSON format to JSON (not used much, we use serialize_doc instead)
from bson.json_util import dumps

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
# Blueprint groups all API routes together
# "api": Blueprint name (used in url_for("api.route_name"))
# __name__: Current module name (routes.routes_api)
# url_prefix="/api": All routes in this blueprint will be prefixed with /api
# Example: @api_bp.route("/books") becomes /api/books
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Enable debug-level logging
# logging.basicConfig(): Configure Python's logging system
# level=logging.DEBUG: Show all log messages (DEBUG, INFO, WARNING, ERROR)
# This helps debug issues during development
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
    
    Example:
        Input: {"_id": ObjectId("123"), "name": "Book"}
        Output: {"_id": "123", "name": "Book"}
    """
    # Line 1: Handle None/null values
    # Check if the document is None (null in JSON)
    if doc is None:
        # Return None if document is empty (no conversion needed)
        return None

    # Line 2: Handle lists - recursively serialize each item
    # isinstance(doc, list) checks if doc is a Python list
    if isinstance(doc, list):
        # List comprehension: call serialize_doc() on each item in the list
        # This handles nested structures like [book1, book2, book3]
        # Each item is processed recursively
        return [serialize_doc(item) for item in doc]

    # Line 3: Handle dictionaries - convert ObjectIds and recurse into nested structures
    # isinstance(doc, dict) checks if doc is a Python dictionary
    if isinstance(doc, dict):
        # Create empty dictionary to store converted values
        result = {}
        
        # Loop through each key-value pair in the dictionary
        # doc.items() returns list of (key, value) tuples
        for key, value in doc.items():
            # Line 3a: MongoDB ObjectIds need to be converted to strings for JSON
            # isinstance(value, ObjectId) checks if value is MongoDB ObjectId type
            if isinstance(value, ObjectId):
                # Convert ObjectId to string using str()
                # Example: ObjectId("507f1f77bcf86cd799439011") → "507f1f77bcf86cd799439011"
                result[key] = str(value)
            
            # Line 3b: Nested lists or dicts need recursive processing
            # isinstance(value, (list, dict)) checks if value is list OR dict
            elif isinstance(value, (list, dict)):
                # Recursively call serialize_doc() on nested structure
                # This handles cases like: {"books": [{"_id": ObjectId(...)}, ...]}
                result[key] = serialize_doc(value)
            
            # Line 3c: Primitive values (strings, numbers, booleans) can be used as-is
            # These don't need conversion - JSON supports them directly
            else:
                # Copy value as-is (string, int, float, bool, None)
                result[key] = value
        
        # Return the converted dictionary
        return result

    # Line 4: Primitive values (strings, numbers, booleans) don't need conversion
    # If doc is not None, list, or dict, it's a primitive value
    # Return it unchanged (JSON supports strings, numbers, booleans)
    return doc


def get_current_user_id():
    """
    Retrieve user ID from JWT token if available,
    otherwise fall back to session-based authentication.
    
    This function supports both authentication methods:
    1. JWT tokens (for API calls from mobile apps or external clients)
    2. Flask sessions (for web browser requests)
    
    Returns:
        str: User ID if authenticated, None otherwise
    
    How it works:
    - First tries JWT token (for API clients)
    - If JWT fails or doesn't exist, falls back to Flask session (for web browsers)
    """
    try:
        # Line 1: Try to get user ID from JWT token first (for API authentication)
        # verify_jwt_in_request(optional=True) checks if JWT token exists in request headers
        # optional=True means: don't raise error if JWT is missing (we'll try session instead)
        verify_jwt_in_request(optional=True)
        
        # Line 2: Get user ID from JWT token
        # get_jwt_identity() extracts the user_id from the JWT token
        # Returns user_id if token is valid, None if token is missing/invalid
        user_id = get_jwt_identity()
        
        # Line 3: Check if JWT token contained a user ID
        if user_id:
            # JWT token is valid and contains user_id - return it
            return user_id
    except Exception as e:
        # Line 4: JWT verification failed, but that's OK - we'll try session instead
        # Exception could be: invalid token, expired token, or no token
        # Log error for debugging (but don't crash - we'll try session)
        logging.debug(f"JWT verification failed: {str(e)}")

    # Line 5: Fall back to Flask session (for web browser requests)
    # session.get("user_id") gets user_id from Flask session (set during login)
    # Returns user_id if logged in, None if not logged in
    return session.get("user_id")


def get_current_user_role():
    """
    Retrieve user role from Flask session
    
    This function gets the user's role ("admin" or "student") from the session.
    The role is set during login and stored in session["user_role"].
    
    Returns:
        str: User role ("admin" or "student") if logged in, None otherwise
    
    Usage:
        Used to check if user has admin privileges
    """
    # Get user role from Flask session
    # session.get("user_role") retrieves the role stored during login
    # Returns "admin" or "student" if logged in, None if not logged in
    return session.get("user_role")

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
        # Line 1: Extract login credentials from request
        # request.get_json() reads JSON data from HTTP request body
        # or {} means: if request body is empty/None, use empty dictionary instead
        # This prevents errors if JSON is malformed or missing
        data = request.get_json() or {}
        
        # Line 2: Extract email from request data
        # data.get("email") gets the "email" field from JSON
        # Returns None if "email" key doesn't exist
        email = data.get("email")
        
        # Line 3: Extract password from request data
        # data.get("password") gets the "password" field from JSON
        # Returns None if "password" key doesn't exist
        password = data.get("password")

        # Line 4: Validate that both email and password were provided
        # if not email or not password: checks if either is None or empty string
        # This ensures both fields are present before attempting login
        if not email or not password:
            # Return error response with 400 status code (Bad Request)
            # jsonify() converts Python dict to JSON response
            return jsonify({"message": "Email and password are required"}), 400

        # Line 5: Verify credentials against database
        # verify_user() function:
        #   - Checks if email exists in database
        #   - Verifies password hash matches stored hash
        #   - Returns user dict if valid, None if invalid
        user = verify_user(email, password)

        # Line 6: Check if credentials were valid
        # if user: means user dict was returned (not None)
        if user:
            # Line 6a: Create JWT token for API authentication
            # create_access_token() generates a JSON Web Token
            # identity=str(user["_id"]) sets the token's identity to user ID
            # JWT tokens are used by mobile apps or external API clients
            access_token = create_access_token(identity=str(user["_id"]))

            # Line 6b: Store session data for backward compatibility
            # Flask sessions allow the web app to remember the logged-in user
            # Session data persists across page requests (until logout)
            
            # Make session persist across browser restarts
            # session.permanent = True tells Flask to save session to cookie
            session.permanent = True
            
            # Store user ID in session (used by page routes)
            # str(user["_id"]) converts MongoDB ObjectId to string
            session["user_id"] = str(user["_id"])
            
            # Store email in session (for display in navbar, etc.)
            session["user_email"] = user["email"]
            
            # Store role in session (for admin checks)
            # user["role"] is "admin" or "student"
            session["user_role"] = user["role"]

            # Line 6c: Return success response with token and user info
            # jsonify() converts Python dict to JSON response
            return jsonify({
                "message": "Login successful",           # Success message
                "access_token": access_token,            # JWT token for API calls
                "role": user["role"],                    # User role (admin or student)
                "user_id": str(user["_id"])              # User ID as string
            })

        # Line 7: Credentials were invalid
        # If we reach here, verify_user() returned None (invalid email/password)
        # Return error response with 400 status code
        return jsonify({"message": "Invalid credentials"}), 400

    except Exception as e:
        # Line 8: Handle any unexpected errors
        # This catches database errors, network errors, etc.
        # Log error for debugging (don't expose internal errors to users)
        logging.error(f"Login error: {str(e)}")
        
        # Return generic error message (don't leak internal error details)
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
        # Line 1: Extract user registration data from request
        # request.get_json() reads JSON data from HTTP request body
        # or {} means: if request body is empty/None, use empty dictionary
        data = request.get_json() or {}
        
        # Line 2: Get first name from request data
        # data.get("first_name", "") gets "first_name" field, defaults to "" if missing
        # .strip() removes leading/trailing whitespace (spaces, tabs, newlines)
        first_name = data.get("first_name", "").strip()
        
        # Line 3: Get last name from request data
        # Same as first_name - gets value and removes whitespace
        last_name = data.get("last_name", "").strip()
        
        # Line 4: Get email from request data
        # Gets email and removes whitespace
        email = data.get("email", "").strip()
        
        # Line 5: Get password from request data
        # Note: Don't strip password - spaces might be intentional in password
        # data.get("password", "") gets password, defaults to "" if missing
        password = data.get("password", "")

        # Line 6: Validate required fields - ensure all required data is provided
        # Check if first_name or last_name is empty (after stripping whitespace)
        # if not first_name: True if first_name is "" or None
        if not first_name or not last_name:
            # Return error response - first/last name required
            return jsonify({"message": "First name and last name are required"}), 400

        # Line 7: Validate email was provided
        # Check if email is empty (after stripping whitespace)
        if not email:
            # Return error response - email required
            return jsonify({"message": "Email is required"}), 400

        # Line 8: Validate password strength (minimum 6 characters)
        # Check if password is empty OR shorter than 6 characters
        # len(password) counts number of characters in password string
        if not password or len(password) < 6:
            # Return error response - password too short
            return jsonify({"message": "Password must be at least 6 characters"}), 400

        # Line 9: Create user account in database
        # create_user() function:
        #   - Checks if email already exists (returns None if exists)
        #   - Hashes password using werkzeug.security.generate_password_hash()
        #   - Creates user document in MongoDB
        #   - Returns user dict if successful, None if email already exists
        user = create_user(first_name, last_name, email, password)

        # Line 10: Check if user was created successfully
        # if user: means user dict was returned (not None)
        if user:
            # Line 10a: User created successfully
            # Return success response with 201 status code (Created)
            return jsonify({
                "message": "Account created successfully!",  # Success message
                "success": True                              # Success flag
            }), 201  # 201 = Created (HTTP status code for successful creation)
        else:
            # Line 10b: Email already exists in database
            # create_user() returned None, meaning email is already registered
            # Return error response with 400 status code
            return jsonify({"message": "Email already exists"}), 400

    except Exception as e:
        # Line 11: Handle any unexpected errors
        # This catches database errors, hashing errors, etc.
        # Log error for debugging
        logging.error(f"Signup error: {str(e)}")
        
        # Return generic error message (don't leak internal error details)
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
        # Line 1: Extract query parameters from URL
        # request.args: Dictionary of URL query parameters (e.g., ?available=true&search=harry)
        # .get("available", ""): Get "available" parameter, default to "" if not present
        # .lower(): Convert to lowercase ("True" → "true")
        # == "true": Compare to string "true", result is boolean (True/False)
        # Example: ?available=true → True, ?available=false → False, no param → False
        available_only = request.args.get("available", "").lower() == "true"
        
        # Line 2: Get search query parameter
        # request.args.get("search", ""): Get "search" parameter, default to "" if not present
        # .strip(): Remove leading/trailing whitespace
        # Example: ?search=harry potter → "harry potter"
        search_query = request.args.get("search", "").strip()
        
        # Line 3: Get genre filter parameter
        # request.args.get("genre", ""): Get "genre" parameter, default to "" if not present
        # .strip(): Remove whitespace
        # Example: ?genre=Fantasy → "Fantasy"
        genre_filter = request.args.get("genre", "").strip()
        
        # Line 4: Get language filter parameter
        # request.args.get("language", ""): Get "language" parameter, default to "" if not present
        # .strip(): Remove whitespace
        # Example: ?language=English → "English"
        language_filter = request.args.get("language", "").strip()

        # Step 1: Get base list of books (all books or only available ones)
        # Check if user wants only available books
        if available_only:
            # Line 1a: Fetch only available books
            # get_available_books() queries MongoDB for books where available=True
            # Returns list of book documents
            books = get_available_books()
        else:
            # Line 1b: Fetch all books regardless of availability
            # get_all_books() queries MongoDB for all books (no filter)
            # Returns list of all book documents
            books = get_all_books()

        # Step 2: Apply search filter (if provided)
        # Check if user provided a search query
        if search_query:
            # Line 2a: Filter books by title or author (case-insensitive)
            # List comprehension: creates new list with only matching books
            # [b for b in books if ...]: Loop through books, keep only those matching condition
            # search_query.lower(): Convert search term to lowercase ("Harry" → "harry")
            # b.get("title", ""): Get book's title, default to "" if missing
            # .lower(): Convert title to lowercase for comparison
            # in: Check if search term appears anywhere in title/author
            # or: Match if search term is in title OR author
            books = [b for b in books if 
                    search_query.lower() in b.get("title", "").lower() or      # Check title
                    search_query.lower() in b.get("author", "").lower()]      # Check author

        # Step 3: Apply genre filter (if provided)
        # Check if user selected a genre filter
        if genre_filter:
            # Line 3a: Filter books by genre
            # List comprehension: keep only books matching the genre
            # b.get("genre"): Get book's genre field
            # == genre_filter: Check if genre exactly matches filter
            books = [b for b in books if b.get("genre") == genre_filter]

        # Step 4: Apply language filter (if provided)
        # Check if user selected a language filter
        if language_filter:
            # Line 4a: Filter books by language
            # List comprehension: keep only books matching the language
            # b.get("language"): Get book's language field
            # == language_filter: Check if language exactly matches filter
            books = [b for b in books if b.get("language") == language_filter]

        # Step 5: Convert MongoDB ObjectIds to strings for JSON response
        # serialize_doc() recursively converts all ObjectIds to strings
        # This is necessary because JSON doesn't support MongoDB ObjectId type
        # Example: {"_id": ObjectId("123")} → {"_id": "123"}
        serialized_books = serialize_doc(books)

        # Line 6: Return filtered books as JSON
        # jsonify(): Converts Python dict to JSON HTTP response
        # {"books": serialized_books}: Response format with books array
        # Flask automatically sets Content-Type: application/json header
        return jsonify({"books": serialized_books})

    except Exception as e:
        # Line 7: Handle any unexpected errors
        # This catches database errors, network errors, etc.
        # Log error for debugging
        # f"Error fetching books: {str(e)}": Format string with error message
        logging.error(f"Error fetching books: {str(e)}")
        
        # Return error response with empty books array
        # This prevents frontend from crashing - it gets empty list instead
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
        # Line 1: Get the current user's ID (from session or JWT token)
        # get_current_user_id() tries JWT first, then falls back to Flask session
        # Returns user_id string if logged in, None if not logged in
        user_id = get_current_user_id()
        
        # Line 2: Check if user is logged in
        # if not user_id: True if user_id is None or empty string
        if not user_id:
            # User is not logged in - return error response
            # 401 = Unauthorized (HTTP status code for authentication required)
            return jsonify({"message": "Authentication required", "loans": []}), 401

        # Line 3: Log for debugging (helps track down issues)
        # logging.debug(): Log debug-level message (only shown if DEBUG level enabled)
        # f"...": f-string formatting (inserts variables into string)
        # {user_id}: User ID value
        # {type(user_id)}: Type of user_id (str, ObjectId, etc.)
        logging.debug(f"Fetching loans for user_id: {user_id} (type: {type(user_id)})")

        # Line 4: Fetch user's loans from database
        # get_user_loans() function:
        #   - Queries MongoDB loans collection for this user
        #   - Uses MongoDB $lookup to join with books collection
        #   - Returns list of loan documents, each containing book details
        # Each loan includes: loan fields + nested "book" object with title, author, etc.
        loans = get_user_loans(user_id)
        
        # Line 5: Log how many loans were found (for debugging)
        # len(loans): Count number of items in loans list
        # This helps verify the query worked correctly
        logging.debug(f"Found {len(loans)} loans for user")
        
        # Line 6: Convert MongoDB ObjectIds to strings for JSON response
        # serialize_doc() recursively converts all ObjectIds to strings
        # Loans contain ObjectIds for: user_id, book_id, _id, book._id
        # JSON doesn't support ObjectId, so we convert to strings
        serialized_loans = serialize_doc(loans)

        # Line 7: Return loans as JSON array
        # jsonify(): Converts Python dict to JSON HTTP response
        # {"loans": serialized_loans}: Response format with loans array
        return jsonify({"loans": serialized_loans})

    except Exception as e:
        # Line 8: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error message
        logging.error(f"Error fetching loans: {str(e)}")
        
        # Import traceback module (for full error details)
        import traceback
        
        # Log full stack trace (shows exactly where error occurred)
        # traceback.format_exc(): Returns full error traceback as string
        logging.error(traceback.format_exc())
        
        # Return error response with empty loans array
        # Prevents frontend from crashing
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
        # Line 1: Verify user is logged in
        # get_current_user_id() gets user_id from session or JWT token
        # Returns user_id string if logged in, None if not logged in
        user_id = get_current_user_id()
        
        # Line 2: Check if user is logged in
        if not user_id:
            # User not logged in - return error response
            # 401 = Unauthorized (authentication required)
            return jsonify({"message": "Authentication required"}), 401

        # Line 3: Extract book_id from request body
        # request.get_json(): Reads JSON data from HTTP request body
        # or {}: Use empty dict if JSON is None/malformed
        data = request.get_json() or {}
        
        # Line 4: Extract book_id from JSON data
        # data.get("book_id"): Get "book_id" field from JSON
        # Returns None if "book_id" key doesn't exist
        book_id = data.get("book_id")

        # Line 5: Validate book_id was provided
        # Check if book_id is None or empty string
        if not book_id:
            # book_id missing - return error response
            # 400 = Bad Request (invalid request data)
            return jsonify({"message": "book_id is required"}), 400

        # Line 6: Verify book exists in database
        # get_book_by_id() queries MongoDB for book with matching _id
        # Returns book document if found, None if not found
        book = get_book_by_id(book_id)
        
        # Line 7: Check if book was found
        if not book:
            # Book doesn't exist - return error response
            # 404 = Not Found (resource doesn't exist)
            return jsonify({"message": "Book not found"}), 404

        # Line 8: Check if book is available for borrowing
        # book.get("available"): Get "available" field from book document
        # Returns True if available, False if borrowed, None if field missing
        # if not book.get("available"): True if available is False or None
        if not book.get("available"):
            # Book is not available (someone else borrowed it)
            # Return error response
            # 400 = Bad Request (can't borrow unavailable book)
            return jsonify({"message": "Book is not available"}), 400

        # Line 9: Create loan record in database
        # create_loan() function:
        #   - Creates new document in MongoDB loans collection
        #   - Sets user_id: who borrowed it
        #   - Sets book_id: which book
        #   - Sets borrowed_date: current timestamp
        #   - Sets due_date: 14 days from now
        #   - Sets status: "active"
        #   - Sets returned_date: None (not returned yet)
        # Returns loan document with _id added
        loan = create_loan(user_id, book_id)
        
        # Line 10: Update book availability to False
        # toggle_book_availability() updates book document in database
        # Sets book.available = False (marks as borrowed)
        # Important: This must happen AFTER creating the loan
        # If this fails, we still have the loan record (can be cleaned up later)
        toggle_book_availability(book_id, False)

        # Line 11: Convert ObjectIds to strings for JSON response
        # serialize_doc() converts loan._id, loan.user_id, loan.book_id to strings
        # JSON doesn't support MongoDB ObjectId type
        serialized_loan = serialize_doc(loan)

        # Line 12: Return success response with loan details
        # jsonify(): Converts Python dict to JSON HTTP response
        # {"message": ..., "loan": ...}: Response format
        # 201 = Created (HTTP status code for successful resource creation)
        return jsonify({
            "message": "Book borrowed successfully",  # Success message
            "loan": serialized_loan                   # Loan data
        }), 201

    except Exception as e:
        # Line 13: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error message
        logging.error(f"Error creating loan: {str(e)}")
        
        # Import traceback module (for full error details)
        import traceback
        
        # Log full stack trace (shows exactly where error occurred)
        logging.error(traceback.format_exc())
        
        # Return generic error response
        # 500 = Internal Server Error
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
        # Line 1: Verify user is logged in
        # get_current_user_id() gets user_id from session or JWT token
        user_id = get_current_user_id()
        
        # Line 2: Check if user is logged in
        if not user_id:
            # User not logged in - return error response
            # 401 = Unauthorized
            return jsonify({"message": "Authentication required"}), 401

        # Line 3: Fetch loan from database to verify it exists
        # get_loan_by_id() queries MongoDB for loan with matching _id
        # We need the loan document to:
        #   - Check if loan exists
        #   - Verify it belongs to current user (security check)
        #   - Get book_id to update book availability
        loan = get_loan_by_id(loan_id)
        
        # Line 4: Check if loan was found
        if not loan:
            # Loan doesn't exist - return error response
            # 404 = Not Found
            return jsonify({"message": "Loan not found"}), 404

        # Line 5: Security check - verify the loan belongs to the current user
        # This prevents users from returning other people's loans
        # loan.get("user_id"): Get user_id from loan document (might be ObjectId)
        # str(...): Convert both to strings for comparison
        # !=: Check if they're different
        if str(loan.get("user_id")) != str(user_id):
            # Loan belongs to different user - return error
            # 403 = Forbidden (user doesn't have permission)
            return jsonify({"message": "Unauthorized"}), 403

        # Line 6: Check if book was already returned
        # loan.get("status"): Get status field from loan document
        # == "returned": Check if status is "returned"
        # Prevents duplicate returns (trying to return same book twice)
        if loan.get("status") == "returned":
            # Book already returned - return error response
            # 400 = Bad Request (invalid operation)
            return jsonify({"message": "Book already returned"}), 400

        # Line 7: Update loan status to "returned"
        # return_loan() function updates loan document in database:
        #   - Sets status: "returned"
        #   - Sets returned_date: current timestamp
        # This preserves borrowing history (who borrowed what, when returned)
        return_loan(loan_id)

        # Line 8: Get book_id from loan document
        # loan.get("book_id"): Get book_id field (might be ObjectId type)
        book_id = loan.get("book_id")
        
        # Line 9: Check if book_id exists (safety check)
        if book_id:
            # Line 9a: Convert ObjectId to string
            # str(book_id): Convert book_id to string (if it's ObjectId)
            book_id_str = str(book_id)
            
            # Line 9b: Update book availability to True
            # toggle_book_availability() updates book document in database
            # Sets book.available = True (makes book available for others to borrow)
            # Important: Must happen AFTER updating loan status
            # This makes the book show as "Available" in the UI
            toggle_book_availability(book_id_str, True)

        # Line 10: Return success message
        # jsonify(): Converts Python dict to JSON HTTP response
        # 200 = OK (default status code, successful operation)
        return jsonify({"message": "Book returned successfully"})

    except Exception as e:
        # Line 11: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error for debugging
        logging.error(f"Error returning book: {str(e)}")
        
        # Return generic error response
        # 500 = Internal Server Error
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
        # Line 1: Get the current user's ID (from session or JWT token)
        # get_current_user_id() tries JWT first, then falls back to Flask session
        # Returns user_id string if logged in, None if not logged in
        user_id = get_current_user_id()
        
        # Line 2: Check if user is logged in
        if not user_id:
            # User is not logged in - return error response
            # 401 = Unauthorized (authentication required)
            # "wishlist": []: Return empty array so frontend doesn't crash
            return jsonify({"message": "Authentication required", "wishlist": []}), 401

        # Line 3: Fetch user's wishlist from database
        # get_user_wishlist() queries MongoDB wishlist collection
        # Filters by user_id to get only this user's wishlist items
        # Returns list of wishlist documents, each containing:
        #   - _id: wishlist item ID
        #   - user_id: who added it
        #   - book_id: which book
        #   - added_at: when it was added
        wishlist_items = get_user_wishlist(user_id)
        
        # Line 4: Convert MongoDB ObjectIds to strings for JSON response
        # serialize_doc() recursively converts all ObjectIds to strings
        # Wishlist items contain ObjectIds for: user_id, book_id, _id
        # JSON doesn't support ObjectId type, so we convert to strings
        serialized_wishlist = serialize_doc(wishlist_items)

        # Line 5: Return wishlist as JSON array
        # jsonify(): Converts Python dict to JSON HTTP response
        # {"wishlist": serialized_wishlist}: Response format with wishlist array
        return jsonify({"wishlist": serialized_wishlist})

    except Exception as e:
        # Line 6: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error message
        logging.error(f"Error fetching wishlist: {str(e)}")
        
        # Import traceback module (for full error details)
        import traceback
        
        # Log full stack trace (shows exactly where error occurred)
        logging.error(traceback.format_exc())
        
        # Return error response with empty wishlist array
        # Prevents frontend from crashing
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
        # Line 1: Verify user is logged in
        # get_current_user_id() gets user_id from session or JWT token
        user_id = get_current_user_id()
        
        # Line 2: Check if user is logged in
        if not user_id:
            # User not logged in - return error response
            # 401 = Unauthorized
            return jsonify({"message": "Authentication required"}), 401

        # Line 3: Extract book_id from request body
        # request.get_json(): Reads JSON data from HTTP request body
        # or {}: Use empty dict if JSON is None/malformed
        data = request.get_json() or {}
        
        # Line 4: Extract book_id from JSON data
        # data.get("book_id"): Get "book_id" field from JSON
        # Returns None if "book_id" key doesn't exist
        book_id = data.get("book_id")

        # Line 5: Validate book_id was provided
        # Check if book_id is None or empty string
        if not book_id:
            # book_id missing - return error response
            # 400 = Bad Request
            return jsonify({"message": "book_id is required"}), 400

        # Line 6: Verify book exists in database
        # get_book_by_id() queries MongoDB for book with matching _id
        # Returns book document if found, None if not found
        book = get_book_by_id(book_id)
        
        # Line 7: Check if book was found
        if not book:
            # Book doesn't exist - return error response
            # 404 = Not Found
            return jsonify({"message": "Book not found"}), 404

        # Line 8: Add book to wishlist
        # add_to_wishlist() function:
        #   - Checks if book is already in user's wishlist
        #   - If already exists, returns existing wishlist item (doesn't create duplicate)
        #   - If not exists, creates new wishlist document in MongoDB
        #   - Returns wishlist item document
        wishlist_item = add_to_wishlist(user_id, book_id)
        
        # Line 9: Convert ObjectIds to strings for JSON response
        # serialize_doc() converts wishlist_item._id, user_id, book_id to strings
        # JSON doesn't support MongoDB ObjectId type
        serialized_item = serialize_doc(wishlist_item)

        # Line 10: Return success response with wishlist item
        # jsonify(): Converts Python dict to JSON HTTP response
        # {"message": ..., "wishlist_item": ...}: Response format
        # 201 = Created (HTTP status code for successful resource creation)
        return jsonify({
            "message": "Book added to wishlist",      # Success message
            "wishlist_item": serialized_item          # Wishlist item data
        }), 201

    except Exception as e:
        # Line 11: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error message
        logging.error(f"Error adding to wishlist: {str(e)}")
        
        # Import traceback module (for full error details)
        import traceback
        
        # Log full stack trace (shows exactly where error occurred)
        logging.error(traceback.format_exc())
        
        # Return generic error response
        # 500 = Internal Server Error
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
        # Line 1: Verify user is logged in
        # get_current_user_id() gets user_id from session or JWT token
        # book_id comes from URL parameter: /api/wishlist/<book_id>
        user_id = get_current_user_id()
        
        # Line 2: Check if user is logged in
        if not user_id:
            # User not logged in - return error response
            # 401 = Unauthorized
            return jsonify({"message": "Authentication required"}), 401

        # Line 3: Validate book_id was provided
        # Check if book_id is None or empty string
        # book_id comes from URL, so it should always exist, but check anyway
        if not book_id:
            # book_id missing - return error response
            # 400 = Bad Request
            return jsonify({"message": "book_id is required"}), 400

        # Line 4: Remove book from wishlist
        # remove_from_wishlist() function:
        #   - Queries MongoDB wishlist collection
        #   - Finds document matching user_id AND book_id
        #   - Deletes the document
        #   - Returns True if document was deleted, False if not found
        success = remove_from_wishlist(user_id, book_id)

        # Line 5: Check if removal was successful
        if success:
            # Line 5a: Book was successfully removed
            # Return success response
            # 200 = OK (default status code)
            return jsonify({"message": "Book removed from wishlist"})
        else:
            # Line 5b: Book was not found in wishlist
            # remove_from_wishlist() returned False (document not found)
            # Return error response
            # 404 = Not Found
            return jsonify({"message": "Book not found in wishlist"}), 404

    except Exception as e:
        # Line 6: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error message
        logging.error(f"Error removing from wishlist: {str(e)}")
        
        # Import traceback module (for full error details)
        import traceback
        
        # Log full stack trace (shows exactly where error occurred)
        logging.error(traceback.format_exc())
        
        # Return generic error response
        # 500 = Internal Server Error
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
        # Line 1: Fetch book from database
        # get_book_by_id() queries MongoDB books collection for book with matching _id
        # book_id comes from URL parameter: /api/books/<book_id>
        # Returns book document if found, None if not found
        book = get_book_by_id(book_id)
        
        # Line 2: Check if book was found
        if not book:
            # Book doesn't exist - return error response
            # 404 = Not Found
            return jsonify({"message": "Book not found"}), 404

        # Line 3: Convert MongoDB ObjectIds to strings for JSON response
        # serialize_doc() converts book._id to string
        # JSON doesn't support MongoDB ObjectId type
        serialized_book = serialize_doc(book)

        # Line 4: Return book as JSON
        # jsonify(): Converts Python dict to JSON HTTP response
        # serialized_book: Book document with ObjectIds converted to strings
        # 200 = OK (default status code)
        return jsonify(serialized_book)

    except Exception as e:
        # Line 5: Handle any unexpected errors
        # This catches database errors, ObjectId conversion errors, etc.
        
        # Log error for debugging
        logging.error(f"Error fetching book: {str(e)}")
        
        # Return generic error response
        # 500 = Internal Server Error
        return jsonify({"message": "Error fetching book"}), 500
