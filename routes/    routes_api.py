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
