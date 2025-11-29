import logging
from flask import Blueprint, jsonify, request
from flask import current_app
from models.users_model import verify_user, get_user_by_email, create_user

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Ensure the Blueprint is registered in your main Flask app file
# Example:
# from routes.routes_api import api_bp
# app.register_blueprint(api_bp)

logging.basicConfig(level=logging.DEBUG)

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


# ---------- LOGIN ROUTE ----------
@api_bp.route("/login", methods=["POST"])
def login():
    logging.debug("Received POST request at /api/login")
    data = request.get_json() or {}
    logging.debug(f"Request data: {data}")

    email = data.get("email")
    password = data.get("password")

    user = verify_user(email, password)

    if user:
        return jsonify({
            "message": "Login successful",
            "role": user["role"],
            "user_id": str(user["_id"])
        })

    return jsonify({"message": "Invalid credentials"}), 400


# ---------- SIGNUP ROUTE ----------
@api_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    if get_user_by_email(email):
        return jsonify({"message": "Email already exists"}), 400

    user = create_user(first_name, last_name, email, password)

    return jsonify({
        "message": "Account created successfully",
        "role": user["role"],
        "user_id": str(user["_id"])
    })


# ---------- GET ALL USERS ----------
@api_bp.route("/users", methods=["GET"])
def get_users():
    db = current_app.config["DB"]

    users = list(db.users.find({}))
    
    # Make MongoDB ObjectIDs JSON serializable
    for u in users:
        u["_id"] = str(u["_id"])
    
    return jsonify(users)
