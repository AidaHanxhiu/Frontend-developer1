from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

def get_user_by_email(email):
    db = current_app.config["DB"]
    return db.users.find_one({"email": email})


def create_user(first_name, last_name, email, password):
    db = current_app.config["DB"]
    hashed_pw = generate_password_hash(password)

    user = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_pw,
        "role": "user"
    }

    db.users.insert_one(user)
    return user


def verify_user(email, password):
    user = get_user_by_email(email)

    if user and check_password_hash(user["password"], password):
        return user

    return None
