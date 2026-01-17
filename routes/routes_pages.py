from flask import Blueprint, render_template, session, redirect, url_for, request
from models.books_model import get_all_books, get_book_by_id, get_available_books, search_books, get_books_by_genre
from models.loans_model import get_user_loans, get_active_loans
from models.wishlist_model import get_user_wishlist
from models.requests_model import get_user_requests
from models.genres_model import get_all_genres
from models.reviews_model import get_book_reviews, get_book_rating

pages_bp = Blueprint(
    "pages",
    __name__,
    template_folder="../templates",
    static_folder="../static"
)


def require_login(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("pages.log_in"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


def require_admin(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("pages.log_in"))
        if session.get("user_role") != "admin":
            return redirect(url_for("pages.all_books"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# ---------- AUTH ROUTES ----------

@pages_bp.route("/")
def index():
    """Home page - redirect to login"""
    if "user_id" in session:
        if session.get("user_role") == "admin":
            return redirect(url_for("pages.admin"))
        return redirect(url_for("pages.dashboard"))
    return redirect(url_for("pages.log_in"))


@pages_bp.route("/sign-up")
def sign_up():
    """Sign up page"""
    return render_template("sign-up.html")


@pages_bp.route("/log-in")
def log_in():
    """Login page"""
    return render_template("log-in.html")


@pages_bp.route("/forgot-password")
def forgot_password():
    """Forgot password page"""
    return render_template("forgot-password.html")


@pages_bp.route("/logout")
def logout():
    """Logout route"""
    session.clear()
    return redirect(url_for("pages.log_in"))


# ---------- DASHBOARD ROUTE ----------

@pages_bp.route("/dashboard")
@require_login
def dashboard():
    """User dashboard"""
    user_id = session.get("user_id")
    active_loans = get_active_loans(user_id)
    wishlist_count = len(get_user_wishlist(user_id))
    
    return render_template("dashboard.html", 
                         active_loans=active_loans,
                         wishlist_count=wishlist_count)


# ---------- USER DASHBOARD ROUTES ----------

@pages_bp.route("/my-books")
@require_login
def my_books():
    """My borrowed books page"""
    user_id = session.get("user_id")
    loans = get_user_loans(user_id)
    return render_template("my-books.html", loans=loans)


@pages_bp.route("/my-loans")
@require_login
def my_loans():
    """My loans page (alias for my-books)"""
    return redirect(url_for("pages.my_books"))


@pages_bp.route("/shared-books")
@require_login
def shared_books():
    """Shared books page"""
    return render_template("shared-books.html")


@pages_bp.route("/wish-list")
@require_login
def wish_list():
    """Wishlist page"""
    user_id = session.get("user_id")
    wishlist = get_user_wishlist(user_id)
    return render_template("wish-list.html", wishlist=wishlist)


@pages_bp.route("/my-requests")
@require_login
def my_requests():
    """My requests page"""
    user_id = session.get("user_id")
    requests = get_user_requests(user_id)
    return render_template("my-requests.html", requests=requests)


# ---------- BROWSING ROUTES ----------

@pages_bp.route("/all-books")
def all_books():
    """All books page"""
    books = get_all_books()
    genres = get_all_genres()
    return render_template("all-books.html", books=books, genres=genres)


@pages_bp.route("/search")
def search():
    """Search page"""
    query = request.args.get("q", "")
    books = search_books(query) if query else get_all_books()
    genres = get_all_genres()
    return render_template("search.html", books=books, query=query, genres=genres)


@pages_bp.route("/book/<book_id>")
def book_details(book_id):
    """Book details page"""
    book = get_book_by_id(book_id)
    if not book:
        return redirect(url_for("pages.all_books"))
    
    reviews = get_book_reviews(book_id)
    rating = get_book_rating(book_id)
    
    # Check if in wishlist
    in_wishlist = False
    if "user_id" in session:
        from models.wishlist_model import is_in_wishlist
        in_wishlist = is_in_wishlist(session["user_id"], book_id)
    
    return render_template("book_details.html", 
                         book=book, 
                         reviews=reviews, 
                         rating=rating,
                         in_wishlist=in_wishlist)


@pages_bp.route("/borrow/<book_id>")
@require_login
def borrow(book_id):
    """Borrow book page"""
    book = get_book_by_id(book_id)
    if not book:
        return redirect(url_for("pages.all_books"))
    
    return render_template("borrow.html", book=book)


@pages_bp.route("/all-genres")
def all_genres():
    """All genres page"""
    genres = get_all_genres()
    return render_template("all-genres.html", genres=genres)


@pages_bp.route("/all-languages")
def all_languages():
    """All languages page"""
    return render_template("all-languages.html")


# ---------- ADMIN ----------

@pages_bp.route("/admin")
@require_admin
def admin():
    """Admin dashboard"""
    books = get_all_books()
    from models.users_model import get_all_users
    users = get_all_users()
    
    stats = {
        "total_books": len(books),
        "available_books": len([b for b in books if b.get("available", False)]),
        "borrowed_books": len([b for b in books if not b.get("available", False)]),
        "total_users": len(users)
    }
    
    return render_template("admin.html", books=books, users=users, stats=stats)


@pages_bp.route("/admin/users")
@require_admin
def admin_users():
    """Admin users management page"""
    from models.users_model import get_all_users
    users = get_all_users()
    return render_template("admin_users.html", users=users)
