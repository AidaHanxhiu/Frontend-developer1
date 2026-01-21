# This file contains all the page routes (routes that render HTML templates)
# Page routes are different from API routes:
# - Page routes: Return HTML pages (e.g., /all-books returns all-books.html)
# - API routes: Return JSON data (e.g., /api/books returns book data)
# 
# When a user visits a URL like /all-books, Flask finds the matching route here
# The route function fetches data from the database and passes it to the HTML template
# The template then renders the data into HTML that the user sees in their browser

from flask import Blueprint, render_template, session, redirect, url_for, request
from models.books_model import get_all_books, get_book_by_id, get_available_books, search_books, get_books_by_genre
from models.loans_model import get_user_loans, get_active_loans
from models.wishlist_model import get_user_wishlist
from models.requests_model import get_user_requests
from models.genres_model import get_all_genres
from models.reviews_model import get_book_reviews, get_book_rating

# Create a Blueprint to organize page routes
# Blueprints help organize code by grouping related routes together
# All routes in this file are part of the "pages" blueprint
pages_bp = Blueprint(
    "pages",
    __name__,
    template_folder="../templates",
    static_folder="../static"
)


# DECORATOR: require_login
# This decorator protects routes that require the user to be logged in
# When applied to a route function, it checks if user_id exists in the session
# If not logged in, redirects to login page; otherwise allows access to the route
# Example: @require_login means only logged-in users can access that page
def require_login(f):
    """Decorator to require login"""
    def decorated_function(*args, **kwargs):
        # Check if user is logged in by looking for user_id in session
        # Session stores user information after successful login
        if "user_id" not in session:
            # Not logged in - redirect to login page
            return redirect(url_for("pages.log_in"))
        # Logged in - allow access to the route
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# DECORATOR: require_admin
# This decorator protects routes that only admins can access
# It checks both: 1) user is logged in, 2) user has admin role
# Used for admin-only pages like the admin panel
def require_admin(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        # First check if user is logged in
        if "user_id" not in session:
            return redirect(url_for("pages.log_in"))
        # Then check if user has admin role
        # Regular users are redirected to all-books page
        if session.get("user_role") != "admin":
            return redirect(url_for("pages.all_books"))
        # User is admin - allow access
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


@pages_bp.route("/reset-password/<token>")
def reset_password_page(token):
    """Reset password page with token verification"""
    # Import password reset functions
    from models.users_model import verify_reset_token
    
    # Verify token is valid (not expired and not used)
    token_doc = verify_reset_token(token)
    if not token_doc:
        # Token is invalid - show error message
        return render_template("reset-password.html", valid_token=False, token=token)
    
    # Token is valid - show password reset form
    return render_template("reset-password.html", valid_token=True, token=token)


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

# ROUTE: /my-books
# This page shows all books that the logged-in user has borrowed
# It displays both active loans (currently borrowed) and returned loans (history)
# The page uses JavaScript to fetch loan data from /api/loans and display it
@pages_bp.route("/my-books")
@require_login  # Only logged-in users can access this page
def my_books():
    """My borrowed books page"""
    # Get the current user's ID from the session (set during login)
    user_id = session.get("user_id")
    # Fetch all loans for this user from the database
    # get_user_loans() uses $lookup to join loans with books collection
    # This gives us book title, author, etc. along with loan details
    loans = get_user_loans(user_id)
    # Pass the loans data to the template
    # The template's JavaScript will fetch from /api/loans to display them
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

# ROUTE: /all-books
# This is the main catalog page where users can browse all books in the library
# It shows all books with their availability status (Available/Borrowed)
# Users can filter by availability, search, genre, or language
# The page uses JavaScript to fetch books from /api/books and display them dynamically
@pages_bp.route("/all-books")
def all_books():
    """All books page"""
    # Fetch all books from the database (used for initial page load)
    # The JavaScript on the page will fetch from /api/books for filtering/searching
    books = get_all_books()
    # Get all genres for the filter dropdown
    genres = get_all_genres()
    # Pass books and genres to the template
    # The template uses JavaScript to fetch updated book data from the API
    return render_template("all-books.html", books=books, genres=genres)


@pages_bp.route("/search")
def search():
    """Search page"""
    query = request.args.get("q", "")
    books = search_books(query) if query else get_all_books()
    genres = get_all_genres()
    return render_template("search.html", books=books, query=query, genres=genres)


# ROUTE: /book/<book_id>
# This page shows detailed information about a specific book
# Users can view book details, check availability, borrow the book, add to wishlist, and see reviews
# The book_id comes from the URL (e.g., /book/12345)
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
