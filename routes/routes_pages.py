from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)

@pages_bp.route("/admin")
def admin():
    return render_template("admin.html")

@pages_bp.route("/all-books")
def all_books():
    return render_template("all-books.html")

@pages_bp.route("/all-genres")
def all_genres():
    return render_template("all-genres.html")

@pages_bp.route("/all-languages")
def all_languages():
    return render_template("all-languages.html")

@pages_bp.route("/forgot-password")
def forgot_password():
    return render_template("forgot-password.html")

@pages_bp.route("/log-in")
def log_in():
    return render_template("log-in.html")

@pages_bp.route("/my-books")
def my_books():
    return render_template("my-books.html")

@pages_bp.route("/shared-books")
def shared_books():
    return render_template("shared-books.html")

@pages_bp.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")

@pages_bp.route("/wish-list")
def wish_list():
    return render_template("wish-list.html")
