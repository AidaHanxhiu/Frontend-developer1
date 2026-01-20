"""
Database initialization script
Run this script to initialize the database with sample data
"""
from models.users_model import create_user
from models.books_model import create_book, get_db
from models.genres_model import create_genre
from models.authors_model import create_author
from models.loans_model import create_loan

def init_database():
    """Initialize database with sample data"""
    print("Initializing database...")
    db = get_db()
    
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
        },
        {
            "title": "To Kill a Mockingbird",
            "author": "Harper Lee",
            "year": 1960,
            "isbn": "978-0061120084",
            "description": "A novel about racial injustice in the Deep South",
            "genre": "Fiction",
            "language": "English",
            "available": True
        },
        {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "year": 1925,
            "isbn": "978-0743273565",
            "description": "A story of the Jazz Age in 1920s America",
            "genre": "Fiction",
            "language": "English",
            "available": True
        },
        {
            "title": "One Hundred Years of Solitude",
            "author": "Gabriel García Márquez",
            "year": 1967,
            "isbn": "978-0060883287",
            "description": "A landmark of magical realism set in Macondo",
            "genre": "Fantasy",
            "language": "Spanish",
            "available": True
        },
        {
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "year": 1937,
            "isbn": "978-0547928227",
            "description": "Bilbo Baggins' adventure to the Lonely Mountain",
            "genre": "Fantasy",
            "language": "English",
            "available": True
        },
        {
            "title": "The Catcher in the Rye",
            "author": "J.D. Salinger",
            "year": 1951,
            "isbn": "978-0316769488",
            "description": "Holden Caulfield's story of teenage alienation",
            "genre": "Fiction",
            "language": "English",
            "available": False
        },
        {
            "title": "The Alchemist",
            "author": "Paulo Coelho",
            "year": 1988,
            "isbn": "978-0061122415",
            "description": "A shepherd's journey to find his personal legend",
            "genre": "Fantasy",
            "language": "Portuguese",
            "available": True
        },
        {
            "title": "The Little Prince",
            "author": "Antoine de Saint-Exupéry",
            "year": 1943,
            "isbn": "978-0156012195",
            "description": "A poetic tale of loneliness, friendship, and love",
            "genre": "Fantasy",
            "language": "French",
            "available": True
        },
        {
            "title": "Sapiens: A Brief History of Humankind",
            "author": "Yuval Noah Harari",
            "year": 2011,
            "isbn": "978-0062316110",
            "description": "A narrative of human history and evolution",
            "genre": "Non-Fiction",
            "language": "English",
            "available": True
        },
        {
            "title": "The Name of the Rose",
            "author": "Umberto Eco",
            "year": 1980,
            "isbn": "978-0156001311",
            "description": "A historical mystery set in an Italian monastery",
            "genre": "Mystery",
            "language": "Italian",
            "available": False
        },
        {
            "title": "Don Quixote",
            "author": "Miguel de Cervantes",
            "year": 1605,
            "isbn": "978-0060934346",
            "description": "The adventures of a man who becomes a knight-errant",
            "genre": "Fiction",
            "language": "Spanish",
            "available": True
        }
    ]
    
    # Insert only new books; keep existing ones untouched
    created_books = []
    existing_isbns = set(
        b.get("isbn")
        for b in db.books.find({}, {"isbn": 1})
        if b.get("isbn")
    )

    for book_data in sample_books:
        isbn = book_data.get("isbn")
        title = book_data.get("title")

        # Skip if a book with the same ISBN already exists
        if isbn and isbn in existing_isbns:
            continue

        # Fallback: if no ISBN, skip if a book with same title already exists
        if not isbn and title and db.books.find_one({"title": title}):
            continue

        created = create_book(book_data)
        created_books.append(created)

    # Create sample loans for the student user
    if student and created_books:
        print("Creating sample loans for student user...")
        # Borrow a few books for the demo student
        for book in created_books[:3]:
            create_loan(str(student["_id"]), str(book["_id"]))
    
    print("\nDatabase initialization complete!")
    print("\nSample credentials:")
    print("Admin: admin@library.com / admin123")
    print("Student: john@example.com / student123")

if __name__ == "__main__":
    init_database()