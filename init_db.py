"""
Database initialization script
Run this script to initialize the database with sample data
"""
from app import get_db
from models.users_model import create_user
from models.books_model import create_book
from models.genres_model import create_genre
from models.authors_model import create_author

def init_database():
    """Initialize database with sample data"""
    db = get_db()
    
    print("Initializing database...")
    
    # Create sample genres
    print("Creating genres...")
    genres = ["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", "Romance", "Biography", "History"]
    for genre_name in genres:
        create_genre(genre_name)
    
    # Create sample authors
    print("Creating authors...")
    authors = [
        {"name": "J.K. Rowling", "bio": "British author, best known for the Harry Potter series"},
        {"name": "George Orwell", "bio": "English novelist and essayist"},
        {"name": "Jane Austen", "bio": "English novelist"},
        {"name": "Mark Twain", "bio": "American writer and humorist"},
        {"name": "Agatha Christie", "bio": "British mystery writer"}
    ]
    for author_data in authors:
        create_author(author_data["name"], author_data.get("bio"))
    
    # Create admin user
    print("Creating admin user...")
    admin = create_user("Admin", "User", "admin@library.com", "admin123", role="admin")
    if admin:
        print(f"Admin created: admin@library.com / admin123")
    
    # Create sample student user
    print("Creating sample student...")
    student = create_user("John", "Doe", "john@example.com", "student123", role="student")
    if student:
        print(f"Student created: john@example.com / student123")
    
    # Create sample books
    print("Creating sample books...")
    sample_books = [
        {
            "title": "Harry Potter and the Philosopher's Stone",
            "author": "J.K. Rowling",
            "year": 1997,
            "isbn": "978-0747532699",
            "description": "The first book in the Harry Potter series",
            "genre": "Fantasy",
            "language": "English",
            "available": True
        },
        {
            "title": "1984",
            "author": "George Orwell",
            "year": 1949,
            "isbn": "978-0452284234",
            "description": "A dystopian novel about totalitarianism",
            "genre": "Fiction",
            "language": "English",
            "available": True
        },
        {
            "title": "Pride and Prejudice",
            "author": "Jane Austen",
            "year": 1813,
            "isbn": "978-0141439518",
            "description": "A romantic novel of manners",
            "genre": "Romance",
            "language": "English",
            "available": True
        },
        {
            "title": "The Adventures of Tom Sawyer",
            "author": "Mark Twain",
            "year": 1876,
            "isbn": "978-0486400778",
            "description": "A novel about a young boy growing up along the Mississippi River",
            "genre": "Fiction",
            "language": "English",
            "available": False
        },
        {
            "title": "Murder on the Orient Express",
            "author": "Agatha Christie",
            "year": 1934,
            "isbn": "978-0062693662",
            "description": "A Hercule Poirot mystery novel",
            "genre": "Mystery",
            "language": "English",
            "available": True
        }
    ]
    
    for book_data in sample_books:
        create_book(book_data)
    
    print("\nDatabase initialization complete!")
    print("\nSample credentials:")
    print("Admin: admin@library.com / admin123")
    print("Student: john@example.com / student123")

if __name__ == "__main__":
    init_database()