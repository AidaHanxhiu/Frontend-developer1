import bcrypt
from app import get_db


db = get_db()
users_collection = db["users"]  # collection name


def get_user_by_email(email):
    return users_collection.find_one({"email": email})


def create_user(first_name, last_name, email, password, role="student"):
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    
    user = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_pw,  # hashed password stored
        "role": role
    }

    users_collection.insert_one(user)
    return user


def verify_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return None
    
    # check hashed password
    if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return user
    
    return None
