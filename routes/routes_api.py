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
    Supports query parameters: available, search, genre, language
    """
    try:
        # Get query parameters
        available_only = request.args.get("available", "").lower() == "true"
        search_query = request.args.get("search", "").strip()
        genre_filter = request.args.get("genre", "").strip()
        language_filter = request.args.get("language", "").strip()

        # Start with all books or available books
        if available_only:
            books = get_available_books()
        else:
            books = get_all_books()

        # Apply search filter
        if search_query:
            # Filter books by title or author (case-insensitive)
            books = [b for b in books if 
                    search_query.lower() in b.get("title", "").lower() or 
                    search_query.lower() in b.get("author", "").lower()]

        # Apply genre filter
        if genre_filter:
            books = [b for b in books if b.get("genre") == genre_filter]

        # Apply language filter
        if language_filter:
            books = [b for b in books if b.get("language") == language_filter]

        # Serialize books (convert ObjectId to string)
        serialized_books = serialize_doc(books)

        return jsonify({"books": serialized_books})

    except Exception as e:
        logging.error(f"Error fetching books: {str(e)}")
        return jsonify({"message": "Error fetching books", "books": []}), 500

# ---------- LOAN ROUTES ----------

@api_bp.route("/loans", methods=["GET"])
def get_user_loans_endpoint():
    """
    Get all loans for the current user
    Returns active and returned loans with book details
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required", "loans": []}), 401

        logging.debug(f"Fetching loans for user_id: {user_id} (type: {type(user_id)})")

        # Get user's loans with book details
        loans = get_user_loans(user_id)
        
        logging.debug(f"Found {len(loans)} loans for user")
        
        # Serialize loans (convert ObjectId to string)
        serialized_loans = serialize_doc(loans)

        return jsonify({"loans": serialized_loans})

    except Exception as e:
        logging.error(f"Error fetching loans: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"message": "Error fetching loans", "loans": []}), 500


@api_bp.route("/loans", methods=["POST"])
def borrow_book():
    """
    Create a new loan (borrow a book)
    Requires: book_id in request body
    Updates book availability to False
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required"}), 401

        data = request.get_json() or {}
        book_id = data.get("book_id")

        if not book_id:
            return jsonify({"message": "book_id is required"}), 400

        # Check if book exists and is available
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404

        if not book.get("available"):
            return jsonify({"message": "Book is not available"}), 400

        # Create the loan using the imported function
        loan = create_loan(user_id, book_id)
        
        # Update book availability to False
        toggle_book_availability(book_id, False)

        # Serialize loan
        serialized_loan = serialize_doc(loan)

        return jsonify({
            "message": "Book borrowed successfully",
            "loan": serialized_loan
        }), 201

    except Exception as e:
        logging.error(f"Error creating loan: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({"message": "Error borrowing book"}), 500


@api_bp.route("/loans/<loan_id>/return", methods=["POST"])
def return_book(loan_id):
    """
    Return a book (mark loan as returned)
    Updates loan status and book availability to True
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"message": "Authentication required"}), 401

        # Get the loan to verify ownership and get book_id
        loan = get_loan_by_id(loan_id)
        
        if not loan:
            return jsonify({"message": "Loan not found"}), 404

        # Verify the loan belongs to the current user
        if str(loan.get("user_id")) != str(user_id):
            return jsonify({"message": "Unauthorized"}), 403

        # Check if already returned
        if loan.get("status") == "returned":
            return jsonify({"message": "Book already returned"}), 400

        # Mark loan as returned
        return_loan(loan_id)

        # Update book availability to True
        book_id = loan.get("book_id")
        if book_id:
            # Convert ObjectId to string if needed
            book_id_str = str(book_id)
            toggle_book_availability(book_id_str, True)

        return jsonify({"message": "Book returned successfully"})

    except Exception as e:
        logging.error(f"Error returning book: {str(e)}")
        return jsonify({"message": "Error returning book"}), 500
