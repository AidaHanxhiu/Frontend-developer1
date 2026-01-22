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
    get_books_by_language         # Fetch by language
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
    """
    if doc is None:
        return None                          # Return None if document is empty

    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]  # Recursively serialize lists

    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)     # Convert ObjectId to string
            elif isinstance(value, (list, dict)):
                result[key] = serialize_doc(value)  # Recursive conversion
            else:
                result[key] = value
        return result

    return doc                               # Return primitive values unchanged


def get_current_user_id():
    """
    Retrieve user ID from JWT token if available,
    otherwise fall back to session-based authentication.
    """
    try:
        verify_jwt_in_request(optional=True)  # Check JWT if present
        user_id = get_jwt_identity()          # Get user ID from token
        if user_id:
            return user_id
    except Exception as e:
        logging.debug(f"JWT verification failed: {str(e)}")  # Log JWT errors

    return session.get("user_id")             # Fallback to session


def get_current_user_role():
    """
    Retrieve user role from session
    """
    return session.get("user_role")           # Used for admin checks

# ---------- AUTHENTICATION ROUTES ----------

@api_bp.route("/login", methods=["POST"])
def login():
    """
    User login with JWT token generation
    """
    try:
        data = request.get_json() or {}        # Read JSON body
        email = data.get("email")              # Extract email
        password = data.get("password")        # Extract password

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = verify_user(email, password)    # Validate credentials

        if user:
            access_token = create_access_token(identity=str(user["_id"]))

            # Store session data for backward compatibility
            session.permanent = True
            session["user_id"] = str(user["_id"])
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]

            return jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "role": user["role"],
                "user_id": str(user["_id"])
            })

        return jsonify({"message": "Invalid credentials"}), 400

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({"message": "Server error"}), 500
