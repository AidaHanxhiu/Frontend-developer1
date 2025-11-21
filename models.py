books = [
    {
        "id": 1,
        "title": "Book A",
        "author": "Author A",
        "year": 2020,
        "genre": "Drama",
        "available": True
    },
    {
        "id": 2,
        "title": "Book B",
        "author": "Author B",
        "year": 2018,
        "genre": "Fantasy",
        "available": False
    }
]

def get_all_books():
    return books

def get_book_by_id(book_id):
    return next((b for b in books if b["id"] == book_id), None)

def add_book(data):
    new_id = max(b["id"] for b in books) + 1
    data["id"] = new_id
    books.append(data)
    return data

