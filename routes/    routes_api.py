from flask import Blueprint, jsonify, request

api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)

# ---------- GET ROUTES ----------

@api_bp.route("/books", methods=["GET"])
def get_books():
    return jsonify({"books": []})

@api_bp.route("/genres", methods=["GET"])
def get_genres():
    return jsonify({"genres": []})

@api_bp.route("/languages", methods=["GET"])
def get_languages():
    return jsonify({"languages": []})

@api_bp.route("/wishlist", methods=["GET"])
def get_wishlist():
    return jsonify({"wishlist": []})


# ---------- POST ROUTES ----------

@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if email == "admin@library.com" and password == "admin123":
        return jsonify({"message": "Admin login successful!"})

    if email == "john@example.com" and password == "student123":
        return jsonify({"message": "Student login successful!"})

    return jsonify({"message": "Invalid credentials"})

@api_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    return jsonify({"message": "User created"})

@api_bp.route("/books/add", methods=["POST"])
def add_book():
    data = request.get_json()
    return jsonify({"message": "Book added"})

@api_bp.route("/wishlist/add", methods=["POST"])
def wishlist_add():
    data = request.get_json()
    return jsonify({"message": "Added to wishlist"})



@api_bp.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    return jsonify({"book_id": book_id, "title": "Example Book"})

@api_bp.route("/books/search", methods=["GET"])
def search_books():
    query = request.args.get("q", "")
    return jsonify({"results": [], "query": query})

@api_bp.route("/user/<int:user_id>/books", methods=["GET"])
def get_user_books(user_id):
    return jsonify({"user_id": user_id, "books": []})

@api_bp.route("/user/<int:user_id>/shared-books", methods=["GET"])
def get_user_shared_books(user_id):
    return jsonify({"user_id": user_id, "shared_books": []})

@api_bp.route("/user/<int:user_id>/wishlist", methods=["GET"])
def get_user_wishlist(user_id):
    return jsonify({"user_id": user_id, "wishlist": []})




@api_bp.route("/books/remove", methods=["POST"])
def remove_book():
    data = request.get_json()
    return jsonify({"message": "Book removed"})

@api_bp.route("/books/update", methods=["POST"])
def update_book():
    data = request.get_json()
    return jsonify({"message": "Book updated"})

@api_bp.route("/books/share", methods=["POST"])
def share_book():
    data = request.get_json()
    return jsonify({"message": "Book shared successfully"})

@api_bp.route("/wishlist/remove", methods=["POST"])
def wishlist_remove():
    data = request.get_json()
    return jsonify({"message": "Removed from wishlist"})

@api_bp.route("/user/update", methods=["POST"])
def update_user():
    data = request.get_json()
    return jsonify({"message": "User updated"})