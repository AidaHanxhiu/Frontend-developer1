"""
Page Routes Module - routes/routes_pages.py

This file contains all the page routes (routes that render HTML templates).
Page routes are different from API routes:
- Page routes: Return HTML pages (e.g., /all-books returns all-books.html)
- API routes: Return JSON data (e.g., /api/books returns book data)

When a user visits a URL like /all-books, Flask finds the matching route here.
The route function fetches data from the database and passes it to the HTML template.
The template then renders the data into HTML that the user sees in their browser.
"""

# Import Flask classes and functions needed for page routes
from flask import Blueprint, render_template, session, redirect, url_for, request
# Blueprint: Groups routes together
# render_template: Renders HTML templates with data
# session: Stores user session data (like user_id after login)
# redirect: Redirects user to another page
# url_for: Generates URLs for routes
# request: Access request data (like query parameters)

# Import database functions from models
# These functions interact with MongoDB to fetch/create/update data
from models.books_model import get_all_books, get_book_by_id, get_available_books, search_books, get_books_by_genre
# get_all_books: Fetch all books from database
# get_book_by_id: Fetch a single book by its ID
# get_available_books: Fetch only books that are available (not borrowed)
# search_books: Search books by title or author
# get_books_by_genre: Fetch books filtered by genre

from models.loans_model import get_user_loans, get_active_loans
# get_user_loans: Fetch all loans for a user (active and returned)
# get_active_loans: Fetch only active (currently borrowed) loans for a user

from models.wishlist_model import get_user_wishlist
# get_user_wishlist: Fetch all books in user's wishlist

from models.requests_model import get_user_requests
# get_user_requests: Fetch all book requests made by a user

from models.genres_model import get_all_genres
# get_all_genres: Fetch all book genres from database

from models.reviews_model import get_book_reviews, get_book_rating
# get_book_reviews: Fetch all reviews for a specific book
# get_book_rating: Calculate average rating for a book

# Create a Blueprint to organize page routes
# Blueprints help organize code by grouping related routes together
# All routes in this file are part of the "pages" blueprint
pages_bp = Blueprint(
    "pages",                        # Blueprint name (used in url_for("pages.route_name"))
    __name__,                       # Current module name (routes.routes_pages)
    template_folder="../templates", # Where to find HTML templates
    static_folder="../static"      # Where to find CSS/JS files
)


# DECORATOR: require_login
# This decorator protects routes that require the user to be logged in
# When applied to a route function, it checks if user_id exists in the session
# If not logged in, redirects to login page; otherwise allows access to the route
# Example: @require_login means only logged-in users can access that page
def require_login(f):
    """
    Decorator function that requires user to be logged in
    
    How decorators work:
    - A decorator is a function that takes another function as input
    - It returns a new function that wraps the original function
    - When you put @require_login above a route, it protects that route
    
    Args:
        f: The route function to protect (e.g., my_books function)
    
    Returns:
        decorated_function: A new function that checks login before calling f
    """
    def decorated_function(*args, **kwargs):
        # *args: Accepts any number of positional arguments (like route parameters)
        # **kwargs: Accepts any number of keyword arguments
        
        # Check if user is logged in by looking for user_id in session
        # Session stores user information after successful login
        # "user_id" not in session means user hasn't logged in yet
        if "user_id" not in session:
            # Not logged in - redirect to login page
            # url_for("pages.log_in") generates the URL for the login route
            return redirect(url_for("pages.log_in"))
        
        # Logged in - allow access to the route
        # Call the original route function with all its arguments
        return f(*args, **kwargs)
    
    # Set the decorated function's name to match the original function's name
    # This is important for Flask's routing system to work correctly
    decorated_function.__name__ = f.__name__
    
    # Return the decorated function (this replaces the original function)
    return decorated_function


# DECORATOR: require_admin
# This decorator protects routes that only admins can access
# It checks both: 1) user is logged in, 2) user has admin role
# Used for admin-only pages like the admin panel
def require_admin(f):
    """
    Decorator function that requires user to be logged in AND have admin role
    
    This decorator does two checks:
    1. Checks if user is logged in (has user_id in session)
    2. Checks if user has "admin" role (not "student")
    
    Args:
        f: The route function to protect (e.g., admin function)
    
    Returns:
        decorated_function: A new function that checks login and admin role
    """
    def decorated_function(*args, **kwargs):
        # *args: Accepts any number of positional arguments
        # **kwargs: Accepts any number of keyword arguments
        
        # First check: Is user logged in?
        # Check if user_id exists in session (set during login)
        if "user_id" not in session:
            # Not logged in - redirect to login page
            return redirect(url_for("pages.log_in"))
        
        # Second check: Does user have admin role?
        # session.get("user_role") gets the role from session (set during login)
        # If role is not "admin", user is a regular student
        if session.get("user_role") != "admin":
            # Regular user trying to access admin page - redirect to all-books
            return redirect(url_for("pages.all_books"))
        
        # User passed both checks: logged in AND admin role
        # Allow access to the admin route
        return f(*args, **kwargs)
    
    # Set the decorated function's name to match the original function's name
    decorated_function.__name__ = f.__name__
    
    # Return the decorated function
    return decorated_function


# ---------- AUTH ROUTES ----------

@pages_bp.route("/")
# @pages_bp.route("/") decorator tells Flask: "When user visits root URL (/), call this function"
# This is the home page route - the first page users see
def index():
    """
    Home page route - redirects users based on their login status and role
    
    Logic:
    - If logged in as admin → redirect to admin page
    - If logged in as student → redirect to dashboard
    - If not logged in → redirect to login page
    """
    # Check if user is logged in by checking if user_id exists in session
    if "user_id" in session:
        # User is logged in - check their role
        # session.get("user_role") gets the role ("admin" or "student")
        if session.get("user_role") == "admin":
            # User is admin - redirect to admin dashboard
            return redirect(url_for("pages.admin"))
        
        # User is logged in but not admin (regular student)
        # Redirect to their dashboard
        return redirect(url_for("pages.dashboard"))
    
    # User is not logged in - redirect to login page
    return redirect(url_for("pages.log_in"))


@pages_bp.route("/sign-up")
# @pages_bp.route("/sign-up") decorator: When user visits /sign-up, call this function
def sign_up():
    """
    Sign up page route - displays the user registration form
    
    This route renders the sign-up.html template which contains:
    - Form fields: first name, last name, email, password
    - JavaScript that submits form to /api/signup endpoint
    """
    # render_template() finds the HTML file in templates/ folder and renders it
    # Returns HTML that the browser displays
    return render_template("sign-up.html")


@pages_bp.route("/log-in")
# @pages_bp.route("/log-in") decorator: When user visits /log-in, call this function
def log_in():
    """
    Login page route - displays the user login form
    
    This route renders the log-in.html template which contains:
    - Form fields: email, password
    - JavaScript that submits form to /api/login endpoint
    """
    # Render the login page HTML template
    return render_template("log-in.html")


@pages_bp.route("/forgot-password")
# @pages_bp.route("/forgot-password") decorator: When user visits /forgot-password, call this function
def forgot_password():
    """
    Forgot password page route - displays password reset form
    
    This route renders the forgot-password.html template which contains:
    - Form field: email
    - JavaScript that sends password reset email
    """
    # Render the forgot password page HTML template
    return render_template("forgot-password.html")


@pages_bp.route("/reset-password/<token>")
# @pages_bp.route("/reset-password/<token>") decorator: When user visits /reset-password/ABC123, call this function
# <token> is a URL parameter - Flask extracts it from the URL and passes it to the function
def reset_password_page(token):
    """
    Reset password page route - displays password reset form if token is valid
    
    This route:
    1. Receives a password reset token from the URL
    2. Verifies the token is valid (not expired, not already used)
    3. Shows password reset form if valid, error message if invalid
    
    Args:
        token: Password reset token from email link (e.g., /reset-password/ABC123XYZ)
    """
    # Import password reset verification function
    # Imported here (not at top) to avoid circular imports
    from models.users_model import verify_reset_token
    
    # Verify token is valid (not expired and not used)
    # verify_reset_token() checks if token exists and hasn't expired
    token_doc = verify_reset_token(token)
    
    # Check if token verification returned a valid token document
    if not token_doc:
        # Token is invalid (expired, already used, or doesn't exist)
        # Show error message in the template
        # valid_token=False tells template to show error message
        # token=token passes token to template (for display in error message)
        return render_template("reset-password.html", valid_token=False, token=token)
    
    # Token is valid - show password reset form
    # valid_token=True tells template to show the password reset form
    # token=token passes token to template (needed to submit password reset)
    return render_template("reset-password.html", valid_token=True, token=token)


@pages_bp.route("/logout")
# @pages_bp.route("/logout") decorator: When user visits /logout, call this function
def logout():
    """
    Logout route - clears user session and redirects to login
    
    This route:
    1. Clears all session data (user_id, user_email, user_role)
    2. Redirects user back to login page
    """
    # Clear all session data
    # This removes: user_id, user_email, user_role, etc.
    # After this, user is effectively logged out
    session.clear()
    
    # Redirect user to login page
    return redirect(url_for("pages.log_in"))


# ---------- DASHBOARD ROUTE ----------

@pages_bp.route("/dashboard")
# @pages_bp.route("/dashboard") decorator: When user visits /dashboard, call this function
@require_login
# @require_login decorator: Only logged-in users can access this page
# If not logged in, user is redirected to login page
def dashboard():
    """
    User dashboard route - displays user's overview page
    
    This route:
    1. Gets user ID from session
    2. Fetches user's active loans (currently borrowed books)
    3. Counts items in user's wishlist
    4. Passes data to dashboard template
    
    Returns:
        HTML: Rendered dashboard.html template with user data
    """
    # Get the current user's ID from session (set during login)
    user_id = session.get("user_id")
    
    # Fetch user's active loans (books currently borrowed)
    # get_active_loans() returns list of loans where status="active"
    active_loans = get_active_loans(user_id)
    
    # Count items in user's wishlist
    # get_user_wishlist() returns list of wishlist items
    # len() counts how many items are in the list
    wishlist_count = len(get_user_wishlist(user_id))
    
    # Render dashboard template with user data
    # active_loans: List of currently borrowed books (for display)
    # wishlist_count: Number of books in wishlist (for display)
    return render_template("dashboard.html", 
                         active_loans=active_loans,
                         wishlist_count=wishlist_count)


# ---------- USER DASHBOARD ROUTES ----------

# ROUTE: /my-books
# This page shows all books that the logged-in user has borrowed
# It displays both active loans (currently borrowed) and returned loans (history)
# The page uses JavaScript to fetch loan data from /api/loans and display it
@pages_bp.route("/my-books")
# @pages_bp.route("/my-books") decorator: When user visits /my-books, call this function
@require_login
# @require_login decorator: Only logged-in users can access this page
# If not logged in, user is redirected to login page
def my_books():
    """
    My borrowed books page route - displays user's loan history
    
    This route:
    1. Gets user ID from session
    2. Fetches all loans for this user (active and returned)
    3. Passes loans to template
    4. Template's JavaScript fetches from /api/loans to display them
    
    Note: The template uses JavaScript to fetch loans, so the loans parameter
    here is mainly for initial page load. The JavaScript handles dynamic updates.
    """
    # Get the current user's ID from the session (set during login)
    # session.get("user_id") retrieves the user_id stored in Flask session
    user_id = session.get("user_id")
    
    # Fetch all loans for this user from the database
    # get_user_loans() uses MongoDB $lookup to join loans with books collection
    # This gives us book title, author, etc. along with loan details
    # Returns list of loan documents, each containing book information
    loans = get_user_loans(user_id)
    
    # Pass the loans data to the template
    # The template's JavaScript will fetch from /api/loans to display them
    # loans=loans passes the loans list to the template
    return render_template("my-books.html", loans=loans)


@pages_bp.route("/my-loans")
# @pages_bp.route("/my-loans") decorator: When user visits /my-loans, call this function
@require_login
# @require_login decorator: Only logged-in users can access this page
def my_loans():
    """
    My loans page route - alias/redirect to my-books page
    
    This route redirects /my-loans to /my-books
    Both URLs show the same page (user's borrowed books)
    """
    # Redirect to my_books route (same page, different URL)
    # url_for("pages.my_books") generates the URL for the my_books function
    return redirect(url_for("pages.my_books"))


@pages_bp.route("/shared-books")
# @pages_bp.route("/shared-books") decorator: When user visits /shared-books, call this function
@require_login
# @require_login decorator: Only logged-in users can access this page
def shared_books():
    """
    Shared books page route - displays books shared by other users
    
    This route renders the shared-books.html template
    (Functionality may not be fully implemented)
    """
    # Render the shared books page template
    return render_template("shared-books.html")


@pages_bp.route("/wish-list")
# @pages_bp.route("/wish-list") decorator: When user visits /wish-list, call this function
@require_login
# @require_login decorator: Only logged-in users can access this page
def wish_list():
    """
    Wishlist page route - displays user's wishlist
    
    This route:
    1. Gets user ID from session
    2. Fetches user's wishlist from database
    3. Passes wishlist to template
    4. Template's JavaScript fetches book details for each wishlist item
    """
    # Get the current user's ID from session (set during login)
    user_id = session.get("user_id")
    
    # Fetch user's wishlist from database
    # get_user_wishlist() returns list of wishlist items (each contains book_id)
    wishlist = get_user_wishlist(user_id)
    
    # Render wishlist template with wishlist data
    # Template's JavaScript will fetch book details for each wishlist item
    return render_template("wish-list.html", wishlist=wishlist)


@pages_bp.route("/my-requests")
# @pages_bp.route("/my-requests") decorator: When user visits /my-requests, call this function
@require_login
# @require_login decorator: Only logged-in users can access this page
def my_requests():
    """
    My requests page route - displays user's book requests
    
    This route:
    1. Gets user ID from session
    2. Fetches user's book requests from database
    3. Passes requests to template for display
    """
    # Get the current user's ID from session (set during login)
    user_id = session.get("user_id")
    
    # Fetch user's book requests from database
    # get_user_requests() returns list of request documents
    requests = get_user_requests(user_id)
    
    # Render my-requests template with requests data
    return render_template("my-requests.html", requests=requests)


# ---------- BROWSING ROUTES ----------

# ROUTE: /all-books
# This is the main catalog page where users can browse all books in the library
# It shows all books with their availability status (Available/Borrowed)
# Users can filter by availability, search, genre, or language
# The page uses JavaScript to fetch books from /api/books and display them dynamically
@pages_bp.route("/all-books")
# @pages_bp.route("/all-books") decorator: When user visits /all-books, call this function
# Note: No @require_login - this page is accessible to everyone (even not logged in)
def all_books():
    """
    All books page route - displays the main book catalog
    
    This route:
    1. Fetches all books from database (for initial page load)
    2. Fetches all genres (for filter dropdown)
    3. Passes data to template
    4. Template's JavaScript fetches from /api/books for filtering/searching
    
    Note: The books parameter is mainly for initial page load.
    The JavaScript handles dynamic filtering and searching via /api/books endpoint.
    """
    # Fetch all books from the database (used for initial page load)
    # get_all_books() returns list of all book documents
    # The JavaScript on the page will fetch from /api/books for filtering/searching
    books = get_all_books()
    
    # Get all genres for the filter dropdown
    # get_all_genres() returns list of genre documents
    # Used to populate the "Genre" filter dropdown in the UI
    genres = get_all_genres()
    
    # Pass books and genres to the template
    # books=books: Passes all books to template (for initial display)
    # genres=genres: Passes all genres to template (for filter dropdown)
    # The template uses JavaScript to fetch updated book data from the API
    return render_template("all-books.html", books=books, genres=genres)


@pages_bp.route("/search")
# @pages_bp.route("/search") decorator: When user visits /search, call this function
# Note: No @require_login - search is accessible to everyone
def search():
    """
    Search page route - displays search results for books
    
    This route:
    1. Gets search query from URL parameter (?q=harry)
    2. Searches books if query provided, otherwise shows all books
    3. Fetches genres for filter dropdown
    4. Passes results to template
    
    URL example: /search?q=harry (searches for "harry")
    """
    # Get search query from URL parameters
    # request.args.get("q", "") gets the "q" parameter from URL (?q=harry)
    # If "q" parameter doesn't exist, returns empty string ""
    query = request.args.get("q", "")
    
    # Search books if query provided, otherwise get all books
    # if query: If query is not empty, search for books matching query
    # else: If query is empty, get all books
    # search_books(query) searches by title or author (case-insensitive)
    books = search_books(query) if query else get_all_books()
    
    # Get all genres for the filter dropdown
    genres = get_all_genres()
    
    # Render search template with results
    # books=books: Search results or all books
    # query=query: The search query (for display in search box)
    # genres=genres: All genres (for filter dropdown)
    return render_template("search.html", books=books, query=query, genres=genres)


# ROUTE: /book/<book_id>
# This page shows detailed information about a specific book
# Users can view book details, check availability, borrow the book, add to wishlist, and see reviews
# The book_id comes from the URL (e.g., /book/12345)
@pages_bp.route("/book/<book_id>")
# @pages_bp.route("/book/<book_id>") decorator: When user visits /book/ABC123, call this function
# <book_id> is a URL parameter - Flask extracts it from the URL and passes it to the function
# Note: No @require_login - book details are visible to everyone
def book_details(book_id):
    """
    Book details page route - displays detailed information about a book
    
    This route:
    1. Fetches book by ID from database
    2. Redirects to all-books if book not found
    3. Fetches reviews and rating for the book
    4. Checks if book is in user's wishlist (if logged in)
    5. Passes all data to template
    
    Args:
        book_id: The ID of the book to display (from URL)
    
    Returns:
        HTML: Rendered book_details.html template with book data
        Redirect: Redirects to all-books if book not found
    """
    # Fetch book from database by ID
    # get_book_by_id() queries MongoDB for book with matching _id
    book = get_book_by_id(book_id)
    
    # Check if book was found
    if not book:
        # Book doesn't exist - redirect to all-books page
        # Prevents showing error page for invalid book IDs
        return redirect(url_for("pages.all_books"))
    
    # Fetch reviews for this book
    # get_book_reviews() returns list of review documents for this book
    reviews = get_book_reviews(book_id)
    
    # Calculate average rating for this book
    # get_book_rating() calculates average of all review ratings
    rating = get_book_rating(book_id)
    
    # Check if book is in user's wishlist (only if user is logged in)
    # Default to False (not in wishlist)
    in_wishlist = False
    
    # Check if user is logged in
    if "user_id" in session:
        # User is logged in - check if book is in their wishlist
        # Import here to avoid circular imports
        from models.wishlist_model import is_in_wishlist
        
        # Check if book is in user's wishlist
        # is_in_wishlist() queries database and returns True/False
        in_wishlist = is_in_wishlist(session["user_id"], book_id)
    
    # Render book details template with all data
    # book=book: Book document with all book information
    # reviews=reviews: List of review documents
    # rating=rating: Average rating (number or None)
    # in_wishlist=in_wishlist: Boolean indicating if book is in user's wishlist
    return render_template("book_details.html", 
                         book=book, 
                         reviews=reviews, 
                         rating=rating,
                         in_wishlist=in_wishlist)


@pages_bp.route("/borrow/<book_id>")
# @pages_bp.route("/borrow/<book_id>") decorator: When user visits /borrow/ABC123, call this function
# <book_id> is a URL parameter - Flask extracts it from the URL
@require_login
# @require_login decorator: Only logged-in users can borrow books
def borrow(book_id):
    """
    Borrow book page route - displays confirmation page for borrowing
    
    This route:
    1. Fetches book by ID from database
    2. Redirects to all-books if book not found
    3. Displays borrow confirmation page
    4. User clicks "Confirm Borrow" button which calls /api/loans POST endpoint
    
    Args:
        book_id: The ID of the book to borrow (from URL)
    
    Returns:
        HTML: Rendered borrow.html template with book data
        Redirect: Redirects to all-books if book not found
    """
    # Fetch book from database by ID
    book = get_book_by_id(book_id)
    
    # Check if book was found
    if not book:
        # Book doesn't exist - redirect to all-books page
        return redirect(url_for("pages.all_books"))
    
    # Render borrow confirmation template with book data
    # book=book: Book document (used to display book info and check availability)
    # Template shows book details and "Confirm Borrow" button
    return render_template("borrow.html", book=book)


@pages_bp.route("/all-genres")
# @pages_bp.route("/all-genres") decorator: When user visits /all-genres, call this function
# Note: No @require_login - genres page is accessible to everyone
def all_genres():
    """
    All genres page route - displays all book genres
    
    This route:
    1. Fetches all genres from database
    2. Passes genres to template for display
    """
    # Fetch all genres from database
    # get_all_genres() returns list of genre documents
    genres = get_all_genres()
    
    # Render all-genres template with genres data
    return render_template("all-genres.html", genres=genres)


@pages_bp.route("/all-languages")
# @pages_bp.route("/all-languages") decorator: When user visits /all-languages, call this function
# Note: No @require_login - languages page is accessible to everyone
def all_languages():
    """
    All languages page route - displays books by language
    
    This route renders the all-languages.html template
    (Languages may be hardcoded in template or fetched dynamically)
    """
    # Render all-languages template
    return render_template("all-languages.html")


# ---------- ADMIN ----------

@pages_bp.route("/admin")
# @pages_bp.route("/admin") decorator: When user visits /admin, call this function
@require_admin
# @require_admin decorator: Only users with admin role can access this page
# Regular users are redirected to all-books page
def admin():
    """
    Admin dashboard route - displays admin control panel
    
    This route:
    1. Fetches all books from database
    2. Fetches all users from database
    3. Calculates statistics (total books, available books, etc.)
    4. Passes data to admin template
    
    Returns:
        HTML: Rendered admin.html template with books, users, and stats
    """
    # Fetch all books from database
    # get_all_books() returns list of all book documents
    books = get_all_books()
    
    # Import user model function (imported here to avoid circular imports)
    from models.users_model import get_all_users
    
    # Fetch all users from database
    # get_all_users() returns list of all user documents
    users = get_all_users()
    
    # Calculate statistics for admin dashboard
    stats = {
        # Total number of books in library
        "total_books": len(books),
        
        # Count books where available=True (available for borrowing)
        # List comprehension: creates list of books where available is True
        # len() counts how many books are in that list
        "available_books": len([b for b in books if b.get("available", False)]),
        
        # Count books where available=False (currently borrowed)
        # List comprehension: creates list of books where available is False
        "borrowed_books": len([b for b in books if not b.get("available", False)]),
        
        # Total number of users in system
        "total_users": len(users)
    }
    
    # Render admin template with all data
    # books=books: All books (for admin to manage)
    # users=users: All users (for admin to manage)
    # stats=stats: Statistics dictionary (for dashboard display)
    return render_template("admin.html", books=books, users=users, stats=stats)


@pages_bp.route("/admin/users")
# @pages_bp.route("/admin/users") decorator: When user visits /admin/users, call this function
@require_admin
# @require_admin decorator: Only users with admin role can access this page
def admin_users():
    """
    Admin users management page route - displays user management interface
    
    This route:
    1. Fetches all users from database
    2. Passes users to template for admin to manage
    
    Returns:
        HTML: Rendered admin_users.html template with user data
    """
    # Import user model function (imported here to avoid circular imports)
    from models.users_model import get_all_users
    
    # Fetch all users from database
    # get_all_users() returns list of all user documents
    users = get_all_users()
    
    # Render admin users template with user data
    return render_template("admin_users.html", users=users)
