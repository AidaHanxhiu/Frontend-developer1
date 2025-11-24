from flask import Blueprint, render_template

pages_bp = Blueprint(
    "pages",
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# ---------- AUTH ROUTES ----------

@pages_bp.route("/")
def index():
    return render_template("sign-up.html")

@pages_bp.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")

@pages_bp.route("/log-in")
def log_in():
    return render_template("log-in.html")

@pages_bp.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

# ---------- USER DASHBOARD ROUTES ----------

@pages_bp.route("/my-books")
def my_books():
    return render_template("my-books.html")

@pages_bp.route("/shared-books")
def shared_books():
    return render_template("shared-books.html")

@pages_bp.route("/wish-list")
def wish_list():
    return render_template("wish-list.html")

# ---------- BROWSING ROUTES ----------

@pages_bp.route("/all-books")
def all_books():
    return render_template("all-books.html")

@pages_bp.route("/all-genres")
def all_genres():
    return render_template("all-genres.html")

@pages_bp.route("/all-languages")
def all_languages():
    return render_template("all-languages.html")

# ---------- ADMIN ----------

@pages_bp.route("/admin")
def admin():
    return render_template("admin.html")


# ---------- API ENDPOINTS ----------

from flask import request, jsonify

# Example GET API (required)
@pages_bp.route("/api/hello", methods=["GET"])
def api_hello():
    return jsonify({"message": "Hello from Flask!"})

# LOGIN POST API (connects to your log-in.js)
@pages_bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    # Demo users (you can replace with database later)
    if email == "admin@library.com" and password == "admin123":
        return jsonify({"message": "Admin login successful!"})

    elif email == "john@example.com" and password == "student123":
        return jsonify({"message": "Student login successful!"})

    else:
        return jsonify({"message": "Invalid credentials"})
