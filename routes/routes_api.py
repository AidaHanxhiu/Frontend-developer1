import logging
from flask import Blueprint, jsonify, request, session
from flask import current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from bson import ObjectId
from bson.json_util import dumps

# Import models
from models.users_model import verify_user, get_user_by_email, create_user, get_all_users, update_user, delete_user
from models.books_model import (
    get_all_books, get_book_by_id, create_book, update_book, delete_book,
    search_books, get_available_books, get_books_by_genre, get_books_by_language
)
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
from models.requests_model import (
    create_request, get_user_requests, get_all_requests, update_request_status, delete_request
)
from models.wishlist_model import (
    add_to_wishlist, get_user_wishlist, remove_from_wishlist, is_in_wishlist
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

api_bp = Blueprint("api", __name__, url_prefix="/api")

logging.basicConfig(level=logging.DEBUG)


# Helper function to serialize MongoDB documents
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, list):
                result[key] = [serialize_doc(item) for item in value]
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc


# Helper function to get user_id from JWT or session
def get_current_user_id():
    """Get user_id from JWT token or session (supports both authentication methods)"""
    # Try to get from JWT token first (if present)
    try:
        # Check if JWT token is present in request (optional verification)
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return user_id
    except:
        # No JWT token or invalid token, fall back to session
        pass
    
    # Fall back to session
    return session.get("user_id")


# Helper function to get user_role from JWT or session
def get_current_user_role():
    """Get user_role from JWT token or session (supports both authentication methods)"""
    # Try to get from session first (JWT doesn't store role by default)
    # In a production app, you might want to store role in JWT claims
    return session.get("user_role")


# ---------- AUTHENTICATION ROUTES ----------

@api_bp.route("/login", methods=["POST"])
def login():
    """Login endpoint with JWT token generation"""
    try:
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = verify_user(email, password)

        if user:
            # Create JWT token
            access_token = create_access_token(identity=str(user["_id"]))
            
            # Keep existing session logic for backward compatibility
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
    except ConnectionError as e:
        return jsonify({"message": f"Database connection error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({"message": f"Error connecting to server: {str(e)}"}), 500


@api_bp.route("/logout", methods=["POST"])
def logout():
    """Logout endpoint"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})


@api_bp.route("/signup", methods=["POST"])
def signup():
    """Signup endpoint"""
    try:
        data = request.get_json() or {}
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        password = data.get("password")

        if not all([first_name, last_name, email, password]):
            return jsonify({"message": "All fields are required"}), 400

        if get_user_by_email(email):
            return jsonify({"message": "Email already exists"}), 400

        user = create_user(first_name, last_name, email, password)
        if user:
            return jsonify({
                "message": "Account created successfully",
                "role": user["role"],
                "user_id": str(user["_id"])
            })
        return jsonify({"message": "Failed to create account"}), 500
    except ConnectionError as e:
        return jsonify({"message": f"Database connection error: {str(e)}"}), 500
    except Exception as e:
        logging.error(f"Signup error: {str(e)}")
        return jsonify({"message": f"Error connecting to server: {str(e)}"}), 500


# ---------- BOOKS ROUTES ----------

@api_bp.route("/books", methods=["GET"])
def get_books():
    """Get all books with optional filters"""
    search_query = request.args.get("search", "")
    genre = request.args.get("genre", "")
    language = request.args.get("language", "")
    available_only = request.args.get("available", "").lower() == "true"

    if search_query:
        books = search_books(search_query)
    elif genre:
        books = get_books_by_genre(genre)
    elif language:
        books = get_books_by_language(language)
    elif available_only:
        books = get_available_books()
    else:
        books = get_all_books()

    return jsonify({"books": serialize_doc(books)})


@api_bp.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    """Get a single book by ID"""
    book = get_book_by_id(book_id)
    if book:
        return jsonify(serialize_doc(book))
    return jsonify({"message": "Book not found"}), 404


@api_bp.route("/books", methods=["POST"])
def add_book():
    """Create a new book (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json() or {}
    book = create_book(data)
    return jsonify(serialize_doc(book)), 201


@api_bp.route("/books/<book_id>", methods=["PUT"])
def update_book_route(book_id):
    """Update a book (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json() or {}
    if update_book(book_id, data):
        book = get_book_by_id(book_id)
        return jsonify(serialize_doc(book))
    return jsonify({"message": "Book not found"}), 404


@api_bp.route("/books/<book_id>", methods=["DELETE"])
def delete_book_route(book_id):
    """Delete a book (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    if delete_book(book_id):
        return jsonify({"message": "Book deleted successfully"})
    return jsonify({"message": "Book not found"}), 404


# ---------- LOANS ROUTES ----------

@api_bp.route("/loans", methods=["GET"])
def get_loans():
    """Get user's loans"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    loans = get_user_loans(user_id)
    return jsonify({"loans": serialize_doc(loans)})


@api_bp.route("/loans/active", methods=["GET"])
def get_active_loans_route():
    """Get user's active loans"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    loans = get_active_loans(user_id)
    return jsonify({"loans": serialize_doc(loans)})


@api_bp.route("/loans", methods=["POST"])
def borrow_book():
    """Borrow a book"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"message": "Book ID required"}), 400

    loan = create_loan(user_id, book_id)
    return jsonify(serialize_doc(loan)), 201


@api_bp.route("/loans/<loan_id>/return", methods=["POST"])
def return_book(loan_id):
    """Return a book"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    if return_loan(loan_id):
        return jsonify({"message": "Book returned successfully"})
    return jsonify({"message": "Loan not found"}), 404


# ---------- WISHLIST ROUTES ----------

@api_bp.route("/wishlist", methods=["GET"])
def get_wishlist():
    """Get user's wishlist"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    wishlist = get_user_wishlist(user_id)
    return jsonify({"wishlist": serialize_doc(wishlist)})


@api_bp.route("/wishlist", methods=["POST"])
def add_to_wishlist_route():
    """Add book to wishlist"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"message": "Book ID required"}), 400

    item = add_to_wishlist(user_id, book_id)
    return jsonify(serialize_doc(item)), 201


@api_bp.route("/wishlist/<book_id>", methods=["DELETE"])
def remove_from_wishlist_route(book_id):
    """Remove book from wishlist"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    if remove_from_wishlist(user_id, book_id):
        return jsonify({"message": "Removed from wishlist"})
    return jsonify({"message": "Not found"}), 404


# ---------- PUBLISHERS ROUTES (NEW CLASS) ----------

@api_bp.route("/publishers", methods=["GET"])
def get_publishers():
    """Get all publishers"""
    publishers = get_all_publishers()
    return jsonify({"publishers": serialize_doc(publishers)})


@api_bp.route("/publishers/<publisher_id>", methods=["GET"])
def get_publisher(publisher_id):
    """Get a single publisher by ID"""
    publisher = get_publisher_by_id(publisher_id)
    if publisher:
        return jsonify(serialize_doc(publisher))
    return jsonify({"message": "Publisher not found"}), 404


@api_bp.route("/publishers", methods=["POST"])
def add_publisher():
    """Create a new publisher (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json() or {}
    try:
        publisher = create_publisher(data)
    except ValueError as e:
        return jsonify({"message": str(e)}), 400

    return jsonify(serialize_doc(publisher)), 201


@api_bp.route("/publishers/<publisher_id>", methods=["PUT"])
def update_publisher_route(publisher_id):
    """Update a publisher (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json() or {}
    if update_publisher(publisher_id, data):
        publisher = get_publisher_by_id(publisher_id)
        return jsonify(serialize_doc(publisher))
    return jsonify({"message": "Publisher not found"}), 404


@api_bp.route("/publishers/<publisher_id>", methods=["DELETE"])
def delete_publisher_route(publisher_id):
    """Delete a publisher (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    if delete_publisher(publisher_id):
        return jsonify({"message": "Publisher deleted successfully"})
    return jsonify({"message": "Publisher not found"}), 404


# ---------- RESERVATIONS ROUTES (NEW CLASS) ----------

@api_bp.route("/reservations", methods=["GET"])
def get_reservations():
    """Get user's reservations or all reservations (admin)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    user_role = get_current_user_role()
    if user_role == "admin":
        reservations = get_all_reservations()
    else:
        reservations = get_user_reservations(user_id)

    return jsonify({"reservations": serialize_doc(reservations)})


@api_bp.route("/reservations", methods=["POST"])
def create_reservation_route():
    """Create a reservation for a book"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    data = request.get_json() or {}
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"message": "Book ID required"}), 400

    reservation = create_reservation(user_id, book_id)
    return jsonify(serialize_doc(reservation)), 201


@api_bp.route("/reservations/<reservation_id>", methods=["PUT"])
def update_reservation_route(reservation_id):
    """Update reservation (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json() or {}
    if update_reservation(reservation_id, data):
        reservation = get_reservation_by_id(reservation_id)
        return jsonify(serialize_doc(reservation))
    return jsonify({"message": "Reservation not found"}), 404


@api_bp.route("/reservations/<reservation_id>", methods=["DELETE"])
def delete_reservation_route(reservation_id):
    """Delete a reservation"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    if delete_reservation(reservation_id):
        return jsonify({"message": "Reservation deleted successfully"})
    return jsonify({"message": "Reservation not found"}), 404


# ---------- REQUESTS ROUTES ----------

@api_bp.route("/requests", methods=["GET"])
def get_requests():
    """Get user's requests or all requests (admin)"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    user_role = get_current_user_role()
    if user_role == "admin":
        requests = get_all_requests()
    else:
        requests = get_user_requests(user_id)

    return jsonify({"requests": serialize_doc(requests)})


@api_bp.route("/requests", methods=["POST"])
def create_request_route():
    """Create a book request"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    data = request.get_json() or {}
    request_obj = create_request(
        user_id,
        data.get("book_title"),
        data.get("author"),
        data.get("reason")
    )
    return jsonify(serialize_doc(request_obj)), 201


@api_bp.route("/requests/<request_id>", methods=["DELETE"])
def delete_request_route(request_id):
    """Delete a request"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    if delete_request(request_id):
        return jsonify({"message": "Request deleted successfully"})
    return jsonify({"message": "Request not found"}), 404


# ---------- REVIEWS ROUTES ----------

@api_bp.route("/books/<book_id>/reviews", methods=["GET"])
def get_reviews(book_id):
    """Get reviews for a book"""
    reviews = get_book_reviews(book_id)
    rating = get_book_rating(book_id)
    return jsonify({
        "reviews": serialize_doc(reviews),
        "average_rating": rating
    })


@api_bp.route("/books/<book_id>/reviews", methods=["POST"])
def add_review(book_id):
    """Add a review for a book"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    data = request.get_json() or {}
    rating = data.get("rating")
    comment = data.get("comment")

    if not rating or not (1 <= rating <= 5):
        return jsonify({"message": "Rating must be between 1 and 5"}), 400

    review = create_review(user_id, book_id, rating, comment)
    return jsonify(serialize_doc(review)), 201


@api_bp.route("/reviews", methods=["GET"])
def list_reviews():
    """Get all reviews"""
    reviews = get_all_reviews()
    return jsonify({"reviews": serialize_doc(reviews)})


@api_bp.route("/reviews/<review_id>", methods=["GET"])
def get_review(review_id):
    """Get a single review by ID"""
    review = get_review_by_id(review_id)
    if review:
        return jsonify(serialize_doc(review))
    return jsonify({"message": "Review not found"}), 404


@api_bp.route("/reviews/<review_id>", methods=["PUT"])
def update_review_route(review_id):
    """Update a review"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    data = request.get_json() or {}
    rating = data.get("rating")
    comment = data.get("comment")

    if rating is not None and not (1 <= rating <= 5):
        return jsonify({"message": "Rating must be between 1 and 5"}), 400

    if update_review(review_id, rating=rating, comment=comment):
        review = get_review_by_id(review_id)
        return jsonify(serialize_doc(review))
    return jsonify({"message": "Review not found"}), 404


@api_bp.route("/reviews/<review_id>", methods=["DELETE"])
def delete_review_route(review_id):
    """Delete a review"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"message": "Not authenticated"}), 401

    if delete_review(review_id):
        return jsonify({"message": "Review deleted successfully"})
    return jsonify({"message": "Review not found"}), 404


# ---------- GENRES ROUTES ----------

@api_bp.route("/genres", methods=["GET"])
def get_genres():
    """Get all genres"""
    genres = get_all_genres()
    return jsonify({"genres": serialize_doc(genres)})


# ---------- AUTHORS ROUTES ----------

@api_bp.route("/authors", methods=["GET"])
def get_authors():
    """Get all authors"""
    authors = get_all_authors()
    return jsonify({"authors": serialize_doc(authors)})


# ---------- LANGUAGES ROUTES ----------

@api_bp.route("/languages", methods=["GET"])
def get_languages():
    """Get all available languages"""
    languages = ["English", "Albanian", "Spanish", "French", "German"]
    return jsonify({"languages": languages})


# ---------- USERS ROUTES (ADMIN) ----------

@api_bp.route("/users", methods=["GET"])
def get_users():
    """Get all users (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    users = get_all_users()
    return jsonify({"users": serialize_doc(users)})


@api_bp.route("/users/<user_id>", methods=["PUT"])
def update_user_route(user_id):
    """Update a user (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json() or {}
    if update_user(user_id, data):
        return jsonify({"message": "User updated successfully"})
    return jsonify({"message": "User not found"}), 404


@api_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user_route(user_id):
    """Delete a user (admin only)"""
    user_role = get_current_user_role()
    if user_role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    if delete_user(user_id):
        return jsonify({"message": "User deleted successfully"})
    return jsonify({"message": "User not found"}), 404


# ---------- SAMPLE PROTECTED ENDPOINT WITH JWT ----------

@api_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Sample protected endpoint using JWT authentication only"""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"message": "Invalid token"}), 401
        
        from models.users_model import get_user_by_id
        user = get_user_by_id(user_id)
        if user:
            return jsonify({
                "user_id": str(user["_id"]),
                "email": user["email"],
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "role": user.get("role")
            })
        return jsonify({"message": "User not found"}), 404
    except Exception as e:
        logging.error(f"Profile error: {str(e)}")
        return jsonify({"message": "Error retrieving profile"}), 500
