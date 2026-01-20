# Library Management System

A comprehensive Library Management System built with Flask and MongoDB for a university project.

## Features

### HTML Pages (8+ total)
- ✅ `login.html` - User authentication
- ✅ `dashboard.html` - User dashboard with stats
- ✅ `search.html` - Advanced book search with filters
- ✅ `book_details.html` - Detailed book view with reviews
- ✅ `borrow.html` - Book borrowing interface
- ✅ `my_loans.html` - User's loan history
- ✅ `wishlist.html` - User wishlist management
- ✅ `my_requests.html` - Book request system
- ✅ `admin.html` - Admin CRUD for books and users
- ✅ Additional pages: `all-books.html`, `all-genres.html`, `all-languages.html`, `shared-books.html`, `forgot-password.html`

### MongoDB Collections (8 total)
- ✅ `users` - User accounts with authentication
- ✅ `books` - Book catalog
- ✅ `loans` - Book loan records
- ✅ `requests` - Book requests from users
- ✅ `wishlist` - User wishlists
- ✅ `reviews` - Book reviews and ratings
- ✅ `authors` - Author information
- ✅ `genres` - Genre categories

### CRUD Operations
- ✅ **Books CRUD** - Full Create, Read, Update, Delete for books (Admin)
- ✅ **Users CRUD** - Full Create, Read, Update, Delete for users (Admin)
- ✅ **Loans Management** - Create loans, return books, view history
- ✅ **Wishlist Management** - Add/remove books from wishlist
- ✅ **Reviews System** - Add reviews and ratings for books
- ✅ **Requests System** - Submit and manage book requests

### JavaScript Features
- ✅ **Wishlist Button** - Toggle wishlist items with AJAX
- ✅ **Rating System** - Star-based rating with reviews
- ✅ **Search Filtering** - Real-time search with genre/language filters
- ✅ **Form Validation** - Client-side validation for all forms
- ✅ **Modals** - Bootstrap modals for book details and editing

### Bootstrap Components (10+)
- ✅ Navbar - Responsive navigation with dropdown
- ✅ Cards - Book displays and information cards
- ✅ Forms - Styled form inputs and validation
- ✅ Modals - Edit book modal
- ✅ Grids - Responsive Bootstrap grid system
- ✅ Alerts - Success/error/info messages
- ✅ Buttons - Styled action buttons
- ✅ Pagination - Page navigation (ready for implementation)
- ✅ Badges - Status indicators
- ✅ Input Groups - Search and filter inputs

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB (local or MongoDB Atlas)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Frontend-developer1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure MongoDB**
   
   A `.env` file has been created with the MongoDB Atlas connection string. 
   **IMPORTANT**: You must edit the `.env` file and replace `<db_username>` and `<db_password>` with your actual MongoDB credentials.
   
   The connection string format:
   ```
   MONGODB_URI=mongodb+srv://<db_username>:<db_password>@cluster0.x8mua2a.mongodb.net/library?retryWrites=true&w=majority
   ```
   
   The database name is set to `library` as specified in the connection string.
   
   **Test the connection** (optional):
   ```bash
   python3 test_connection.py
   ```

4. **Initialize the database**
   ```bash
   python init_db.py
   ```
   This will create:
   - Admin user: `admin@library.com` / `admin123`
   - Sample student: `john@example.com` / `student123`
   - Sample books, genres, and authors

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open browser: `http://localhost:5000`
   - Login with admin credentials or create a new account

## Project Structure

```
Frontend-developer1/
├── app.py                 # Main Flask application
├── init_db.py            # Database initialization script
├── requirements.txt      # Python dependencies
├── models/               # Data models
│   ├── models.py        # Legacy models (can be removed)
│   ├── users_model.py   # User CRUD operations
│   ├── books_model.py   # Book CRUD operations
│   ├── loans_model.py   # Loan management
│   ├── requests_model.py # Request management
│   ├── wishlist_model.py # Wishlist operations
│   ├── reviews_model.py  # Review and rating system
│   ├── authors_model.py  # Author management
│   └── genres_model.py   # Genre management
├── routes/               # Flask routes
│   ├── __init__.py      # Blueprint registration
│   ├── routes_api.py    # API endpoints
│   └── routes_pages.py  # Page routes
├── templates/            # HTML templates
│   ├── base.html        # Base template with Bootstrap navbar
│   ├── dashboard.html   # User dashboard
│   ├── login.html       # Login page
│   ├── search.html      # Search page
│   ├── book_details.html # Book details with reviews
│   ├── borrow.html      # Borrow book page
│   ├── my_loans.html    # Loan history
│   ├── wishlist.html    # Wishlist page
│   ├── my_requests.html # Request management
│   └── admin.html       # Admin dashboard
└── static/              # Static files (CSS, JS)
    ├── main.css         # Global styles
    └── [page-specific CSS files]
```

## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `POST /api/signup` - User registration

### Books
- `GET /api/books` - Get all books (with filters)
- `GET /api/books/<id>` - Get book by ID
- `POST /api/books` - Create book (admin)
- `PUT /api/books/<id>` - Update book (admin)
- `DELETE /api/books/<id>` - Delete book (admin)

### Loans
- `GET /api/loans` - Get user's loans
- `GET /api/loans/active` - Get active loans
- `POST /api/loans` - Borrow a book
- `POST /api/loans/<id>/return` - Return a book

### Wishlist
- `GET /api/wishlist` - Get user's wishlist
- `POST /api/wishlist` - Add to wishlist
- `DELETE /api/wishlist/<book_id>` - Remove from wishlist

### Reviews
- `GET /api/books/<id>/reviews` - Get book reviews
- `POST /api/books/<id>/reviews` - Add review

### Requests
- `GET /api/requests` - Get requests
- `POST /api/requests` - Create request
- `DELETE /api/requests/<id>` - Delete request

### Admin
- `GET /api/users` - Get all users (admin)
- `PUT /api/users/<id>` - Update user (admin)
- `DELETE /api/users/<id>` - Delete user (admin)

## Session Management

The application uses Flask sessions for authentication:
- Sessions are permanent (7 days)
- User ID, email, and role are stored in session
- Protected routes use `@require_login` decorator
- Admin routes use `@require_admin` decorator

## Testing

### Test Credentials
- **Admin**: `admin@library.com` / `admin123`
- **Student**: `john@example.com` / `student123`

### Test Flow
1. Login as admin
2. Add books through admin panel
3. Logout and login as student
4. Browse books, add to wishlist
5. Borrow books
6. Add reviews
7. Submit book requests

## Requirements Met

✅ **8+ HTML Pages** - All required pages implemented  
✅ **8 MongoDB Collections** - All collections with CRUD operations  
✅ **Flask Backend** - Complete routing structure with sessions  
✅ **2 Full CRUD Implementations** - Books and Users  
✅ **4+ JavaScript Features** - Wishlist, ratings, search, validation, modals  
✅ **10+ Bootstrap Components** - Navbar, cards, forms, modals, grids, alerts, buttons, pagination, badges, input groups  
✅ **Functional Navigation** - Bootstrap navbar on all pages  
✅ **Session Management** - Login/logout with role-based access  

## Notes

- The application uses Bootstrap 5.3 for styling
- MongoDB ObjectIDs are serialized to strings in API responses
- Password hashing uses Werkzeug's security utilities
- All forms include client-side validation
- Error handling is implemented throughout

## Future Enhancements

- Email service for password reset
- Book sharing functionality
- Advanced search with filters
- Pagination for large lists
- Image upload for book covers
- Export functionality for reports

## Team

### Author
**Anela Beqiri** - Full Stack Developer

### Roles and Contributions
This project was developed individually with the following responsibilities:

- **Backend Development** (Flask & Python)
  - Implemented Flask application with Blueprint architecture
  - Created 40+ RESTful API endpoints
  - Developed JWT-based authentication and authorization system
  - Implemented role-based access control (Admin/Student)

- **Database Design & Management** (MongoDB)
  - Designed and implemented 10 MongoDB collections
  - Created full CRUD operations for all collections (Authors, Books, Genres, Loans, Users, Wishlist, Requests, Reviews, Publishers, Reservations)
  - Implemented database initialization and seeding scripts
  - Configured MongoDB connection with environment variables

- **Frontend Development** (HTML, CSS, Bootstrap)
  - Created 12+ responsive HTML pages using Jinja2 templates
  - Implemented Bootstrap 5.3 UI with 10+ components (Navbar, Cards, Forms, Modals, Tables, Badges, Buttons, Alerts, Grid, Dropdowns)
  - Designed mobile-first responsive layouts
  - Created custom CSS for enhanced user experience

- **JavaScript Development**
  - Implemented interactive features (Wishlist management, Book requests, Form submissions)
  - Created AJAX requests using Fetch API
  - Developed client-side form validation
  - Implemented JWT token management with localStorage
  - Built dynamic DOM manipulation for real-time updates

- **Testing & Documentation**
  - Wrote comprehensive README with setup instructions
  - Created inline code documentation and docstrings
  - Developed test credentials and testing procedures
  - Documented all API endpoints

**Project Type:** Individual University Project  
**Course:** [Add your course name/code here]  
**Institution:** [Add your university name here]

## License

This project is for educational purposes.
# Minor update for final submission
