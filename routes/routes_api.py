# ---------- IMPORTS ----------
import logging
import sys
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
    delete_user,
    create_password_reset_token,
    verify_reset_token,
    invalidate_reset_token,
    update_user_password
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


# ---------- PASSWORD RESET ROUTES ----------

# POST /api/forgot-password - Generate password reset token (demo mode)
# This endpoint generates a secure token and prints the reset link in console
@api_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Generate password reset token and print reset link in console (demo mode).
    Used by the Forgot Password page.
    """
    try:
        # Get email from request body
        data = request.get_json() or {}
        email = data.get("email")

        # Validate that email is provided
        if not email:
            return jsonify({"message": "Email is required"}), 400

        # Check if user exists in database
        user = get_user_by_email(email)
        if not user:
            # Return success even if user doesn't exist (security: prevents email enumeration)
            # This way attackers can't tell which emails are registered
            return jsonify({"message": "If that email exists, a reset link has been sent"})

        # Generate secure reset token (expires in 1 hour)
        # Token is stored in password_reset_tokens collection
        reset_token = create_password_reset_token(str(user["_id"]))

        # Create the reset link that user will visit
        reset_link = f"http://127.0.0.1:5001/reset-password/{reset_token}"

        # Print reset link in server console (demo mode - no real email sent)
        print("\n" + "="*60)
        print("PASSWORD RESET LINK (DEMO MODE)")
        print("="*60)
        print(f"User: {email}")
        print(f"Reset Link: {reset_link}")
        print(f"Token expires in: 1 hour")
        print("="*60 + "\n")
        sys.stdout.flush()

        # Return success message (same message whether user exists or not)
        return jsonify({
            "message": "If that email exists, a reset link has been sent. Check the server console (terminal) for the demo reset link."
        })

    except Exception as e:
        # Log error and return server error response
        logging.error(f"Error processing forgot password: {str(e)}")
        return jsonify({"message": "Server error"}), 500


# POST /api/reset-password - Reset user password using token
# This endpoint verifies the token and updates the user's password
@api_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Reset user password using reset token.
    Used by the Reset Password page.
    """
    try:
        # Get token and new password from request body
        data = request.get_json() or {}
        token = data.get("token")
        new_password = data.get("new_password")

        # Validate that both token and password are provided
        if not token or not new_password:
            return jsonify({"message": "Token and new password are required"}), 400

        # Validate password meets minimum length requirement
        if len(new_password) < 6:
            return jsonify({"message": "Password must be at least 6 characters"}), 400

        # Verify token is valid (not expired and not used)
        token_doc = verify_reset_token(token)
        if not token_doc:
            # Token is invalid, expired, or already used
            return jsonify({"message": "Invalid or expired reset token"}), 400

        # Get user ID from the token document
        user_id = str(token_doc["user_id"])

        # Update user password in database (password is hashed before storage)
        success = update_user_password(user_id, new_password)
        if not success:
            return jsonify({"message": "Failed to update password"}), 500

        # Invalidate token so it cannot be reused (mark as used)
        invalidate_reset_token(token)

        # Return success message
        return jsonify({"message": "Password reset successfully"})

    except Exception as e:
        # Log error and return server error response
        logging.error(f"Error resetting password: {str(e)}")
        return jsonify({"message": "Server error"}), 500


# ---------- LOANS ROUTES ----------

@api_bp.route("/loans", methods=["GET"])
def get_loans():
    """
    Get all loans for the currently logged-in user
    (used by the My Books / My Borrowed Books page)
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        loans = get_user_loans(user_id)
        loans_serialized = [serialize_doc(loan) for loan in loans]
        return jsonify({"loans": loans_serialized})
    except Exception as e:
        logging.error(f"Error fetching user loans: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/loans", methods=["POST"])
def create_user_loan():
    """
    Create a new loan for the currently logged-in user.
    Used by the Borrow Book page (borrow.html) via POST /api/loans.
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        book_id = data.get("book_id")

        if not book_id:
            return jsonify({"message": "book_id is required"}), 400

        # Ensure book exists and is available
        book = get_book_by_id(book_id)
        if not book:
            return jsonify({"message": "Book not found"}), 404
        if not book.get("available", True):
            return jsonify({"message": "Book is not available"}), 400

        # Create loan and mark book as unavailable
        loan = create_loan(user_id, book_id)
        update_book(book_id, {"available": False})

        return jsonify({"message": "Loan created", "loan": serialize_doc(loan)}), 201
    except Exception as e:
        logging.error(f"Error creating loan: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/loans/<loan_id>/return", methods=["POST"])
def api_return_loan(loan_id):
    """
    Mark a loan as returned for the current user
    (used by the Return Book button on My Books page)
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        success = return_loan(loan_id)
        if success:
            return jsonify({"message": "Book returned successfully"})
        else:
            return jsonify({"message": "Loan not found"}), 404
    except Exception as e:
        logging.error(f"Error returning loan %s: %s", loan_id, str(e))
        return jsonify({"message": "Server error"}), 500


# ---------- WISHLIST ROUTES ----------

@api_bp.route("/wishlist", methods=["GET"])
def get_wishlist():
    """
    Get wishlist items for the currently logged-in user.
    Used by the My Wishlist page (wish-list.html).
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        wishlist = get_user_wishlist(user_id)
        wishlist_serialized = [serialize_doc(item) for item in wishlist]
        return jsonify({"wishlist": wishlist_serialized})
    except Exception as e:
        logging.error(f"Error fetching user wishlist: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/wishlist", methods=["POST"])
def add_wishlist_item():
    """
    Add a book to the current user's wishlist.
    Used by the wishlist button on the book details page.
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json() or {}
    book_id = data.get("book_id")

    if not book_id:
        return jsonify({"message": "book_id is required"}), 400

    try:
        item = add_to_wishlist(user_id, book_id)
        return jsonify({"message": "Added to wishlist", "item": serialize_doc(item)})
    except Exception as e:
        logging.error(f"Error adding to wishlist: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/wishlist/<book_id>", methods=["DELETE"])
def remove_wishlist_item(book_id):
    """
    Remove a book from the current user's wishlist.
    Used by both the wishlist page and the book details page.
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        success = remove_from_wishlist(user_id, book_id)
        if success:
            return jsonify({"message": "Removed from wishlist"})
        else:
            return jsonify({"message": "Item not found"}), 404
    except Exception as e:
        logging.error(f"Error removing from wishlist: {str(e)}")
        return jsonify({"message": "Server error"}), 500


# ---------- BOOKS ROUTES (READ-ONLY FOR WISHLIST) ----------

@api_bp.route("/books", methods=["GET"])
def api_get_books():
    """
    Get books list with optional filters.
    Used by All Books and Search pages.
    """
    try:
        available = request.args.get("available")
        search = request.args.get("search", "").strip()
        genre = request.args.get("genre", "").strip()
        language = request.args.get("language", "").strip()

        # Preserve existing model logic; just choose the right query helper
        if search:
            books = search_books(search)
        elif genre:
            books = get_books_by_genre(genre)
        elif language:
            books = get_books_by_language(language)
        elif available == "true":
            books = get_available_books()
        else:
            books = get_all_books()

        return jsonify({"books": [serialize_doc(b) for b in books]})
    except Exception as e:
        logging.error(f"Error fetching books: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/books", methods=["POST"])
def api_create_book():
    """
    Create a new book.
    Used by Admin Add Book form.
    """
    try:
        data = request.get_json() or {}
        book = create_book(data)
        return jsonify({"message": "Book created", "book": serialize_doc(book)})
    except Exception as e:
        logging.error(f"Error creating book: {str(e)}")
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/books/<book_id>", methods=["GET", "PUT", "DELETE"])
def api_book_detail(book_id):
    """
    Get single book details.
    Also supports update/delete for Admin.
    """
    try:
        if request.method == "GET":
            book = get_book_by_id(book_id)
            if not book:
                return jsonify({"message": "Book not found"}), 404
            return jsonify(serialize_doc(book))

        if request.method == "PUT":
            data = request.get_json() or {}
            success = update_book(book_id, data)
            if success:
                return jsonify({"message": "Book updated"})
            return jsonify({"message": "Book not found"}), 404

        if request.method == "DELETE":
            success = delete_book(book_id)
            if success:
                return jsonify({"message": "Book deleted"})
            return jsonify({"message": "Book not found"}), 404

        return jsonify({"message": "Method not allowed"}), 405
    except Exception as e:
        logging.error(f"Error fetching book %s: %s", book_id, str(e))
        return jsonify({"message": "Server error"}), 500


@api_bp.route("/books/<book_id>/reviews", methods=["POST"])
def api_create_book_review(book_id):
    """
    Create or update a review for a book by the current user.
    Used by book_details.html review form.
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        rating = data.get("rating")
        comment = data.get("comment")

        if rating is None:
            return jsonify({"message": "rating is required"}), 400

        review = create_review(user_id, book_id, rating, comment)
        return jsonify({"message": "Review saved", "review": serialize_doc(review)})
    except Exception as e:
        logging.error(f"Error creating review for book %s: %s", book_id, str(e))
        return jsonify({"message": "Server error"}), 500
