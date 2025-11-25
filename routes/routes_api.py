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
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    # create users_models.py in models folder
    # users_models.py file should have a function called get_all_users() that connects to your db
    # get list of users from users_models.py

    for user in USERS:
        if user["email"] == email and user["password"] == password:
            return jsonify({
                "message": "Login successful",
                "role": user["role"],
                "user_id": user["id"]
            })

    return jsonify({"message": "Invalid credentials"}), 400


# ---------------------------------------------------
# SIGNUP
# ---------------------------------------------------
@api_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # check if user already exists
    for user in USERS:
        if user["email"] == email:
            return jsonify({"message": "Email already exists"}), 400

    # create new user
    new_id = max([u["id"] for u in USERS]) + 1
    new_user = {
        "id": new_id,
        "email": email,
        "password": password,
        "role": "student",
        "first_name": first_name,
        "last_name": last_name
    }

    USERS.append(new_user)

    return jsonify({
        "message": "Account created successfully",
        "role": "student",
        "user_id": new_id
    })


