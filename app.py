from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from routes.routes_pages import pages_bp
from routes.routes_api import api_bp

app = Flask(__name__)
app.secret_key = "supersecret123"  # required for sessions

# ------------------------------
# JWT CONFIGURATION
# ------------------------------
app.config["JWT_SECRET_KEY"] = "jwt-secret-key-change-in-production"  # Change this in production!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # Tokens don't expire (or set to timedelta(hours=24))
jwt = JWTManager(app)

# ------------------------------
# MONGODB CONNECTION
# ------------------------------
app.config["MONGO_URI"] = "mongodb://localhost:27017/librarydb"
mongo = PyMongo(app)

# ------------------------------
# ENSURE REQUIRED COLLECTIONS EXIST
# ------------------------------
# This block runs at startup to explicitly create collections and seed an example document.
with app.app_context():
    db = mongo.db

    # Create collections if they do not exist
    for collection_name in ["publishers", "reviews", "reservations"]:
        try:
            db.create_collection(collection_name)
        except Exception:
            # Collection already exists; ignore
            pass

    # Seed sample documents if they are not already present
    if db.publishers.count_documents({"publisher_id": 1}) == 0:
        db.publishers.insert_one({
            "publisher_id": 1,
            "name": "Penguin",
            "country": "USA",
            "yearFounded": 1927
        })

    if db.reviews.count_documents({"review_id": 1}) == 0:
        db.reviews.insert_one({
            "review_id": 1,
            "book_id": 1,
            "user_id": 1,
            "rating": 5,
            "comment": "Great book!"
        })

    if db.reservations.count_documents({"reservation_id": 1}) == 0:
        db.reservations.insert_one({
            "reservation_id": 1,
            "book_id": 1,
            "user_id": 1,
            "reservedDate": "2025-01-10",
            "status": "pending"
        })

# register blueprints
app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)

# run app
if __name__ == "__main__":
    app.run(debug=True)
