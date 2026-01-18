# ---------- IMPORTS ----------
import logging
from flask import Blueprint, jsonify, request, session, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request
)
from bson import ObjectId
from bson.json_util import dumps

# ---------- MODEL IMPORTS ----------
# User-related database operations
from models.users_model import (
    verify_user,
    get_user_by_email,
    create_user,
    get_all_users,
    update_user,
    delete_user
)

# Book-related database operations
from models.books_model import (
    get_all_books,
    get_book_by_id,
    create_book,
    update_book,
    delete_book,
    search_books,
    get_available_books,
    get_books_by_genre,
    get_books_by_language
)

# Loan and reservation operations
from models.loans_model import (
    create_loan,
    get_user_loans,
    get_active_loans,
    return_loan,
    delete_loan,
    create_reservation,
    get_all_reservations,
    get_reservation_by_id,
    get_user_reservations,
    update_reservation,
    delete_reservation,
)

# Requests, wishlist, reviews, genres, authors
from models.requests_model import (
    create_request,
    get_user_requests,
    get_all_requests,
    update_request_status,
    delete_request
)
from models.wishlist_model import (
    add_to_wishlist,
    get_user_wishlist,
    remove_from_wishlist,
    is_in_wishlist
)
from models.reviews_model import (
    create_review,
    get_all_reviews,
    get_review_by_id,
    get_book_reviews,
    get_book_rating,
    update_review,
    delete_review,
)
from models.genres_model import get_all_genres, create_genre
from models.authors_model import (
    get_all_authors,
    create_publisher,
    get_all_publishers,
    get_publisher_by_id,
    update_publisher,
    delete_publisher,
)

# ---------- API BLUEPRINT ----------
# All API routes are grouped under /api
api_bp = Blueprint("api", __name__, url_prefix="/api")

logging.basicConfig(level=logging.DEBUG)

# ---------- HELPER FUNCTIONS ----------

def serialize_doc(doc):
    """
    Convert MongoDB documents (ObjectId) into JSON-serializable format
    """
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, (list, dict)):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc


def get_current_user_id():
    """
    Retrieve user ID from JWT token if available,
    otherwise fall back to session-based authentication
    """
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return user_id
    except:
        pass

    return session.get("user_id")


def get_current_user_role():
    """
    Retrieve user role from session
    """
    return session.get("user_role")

# ---------- AUTHENTICATION ROUTES ----------

@api_bp.route("/login", methods=["POST"])
def login():
    """
    User login with JWT token generation
    """
    try:
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = verify_user(email, password)

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


@api_bp.route("/logout", methods=["POST"])
def logout():
    """Clear user session"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@api_bp.route("/signup", methods=["POST"])
def signup():
    """
    Create a new user account
    """
    try:
        data = request.get_json() or {}
        if not all(data.get(k) for k in ["first_name", "last_name", "email", "password"]):
            return jsonify({"message": "All fields are required"}), 400

        if get_user_by_email(data["email"]):
            return jsonify({"message": "Email already exists"}), 400

        user = create_user(
            data["first_name"],
            data["last_name"],
            data["email"],
            data["password"]
        )

        return jsonify({
            "message": "Account created successfully",
            "role": user["role"],
            "user_id": str(user["_id"])
        })
    except Exception as e:
        logging.error(f"Signup error: {str(e)}")
        return jsonify({"message": "Server error"}), 500
