# models/user_model.py

def get_all_users():
    """
    Temporary mock function until database is implemented.
    Returns a list of user dictionaries.
    """

    users = [
        {
            "id": 1,
            "email": "test@example.com",
            "password": "12345",
            "role": "user"
        },
        {
            "id": 2,
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin"
        }
    ]

    return users
