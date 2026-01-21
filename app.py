# This is the main Flask application file
# It sets up the web server, database connection, and registers all routes
# When you run "python3 app.py", this file starts the web server

import os
import sys

# Prevent Python from creating .pyc files and __pycache__ directories
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True

import logging
from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from routes.routes_pages import pages_bp
from routes.routes_api import api_bp

# Load environment variables from .env file
# This includes the MongoDB connection string (MONGODB_URI)
load_dotenv()

# Reduce verbose pymongo logging
logging.getLogger("pymongo").setLevel(logging.WARNING)

# Create the Flask application instance
# This is the main object that handles all web requests
app = Flask(__name__)
# Secret key is required for Flask sessions
# Sessions allow the app to remember which user is logged in
app.secret_key = "supersecret123"  # required for sessions

# ------------------------------
# JWT CONFIGURATION
# ------------------------------
# JWT (JSON Web Tokens) are used for API authentication
# When the frontend makes API calls, it includes a JWT token to prove the user is logged in
# The secret key is used to sign and verify tokens
app.config["JWT_SECRET_KEY"] = "jwt-secret-key-change-in-production"  # Change this in production!
# Set token expiration (False means tokens never expire for this demo)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # Tokens don't expire (or set to timedelta(hours=24))
jwt = JWTManager(app)

# ------------------------------
# MONGODB CONNECTION
# ------------------------------
# Connect to MongoDB database using the connection string from .env file
# MongoDB stores all our data: users, books, loans, wishlists, etc.
mongodb_uri = os.getenv("MONGODB_URI")
if not mongodb_uri:
    raise ValueError("MONGODB_URI environment variable is not set. Please check your .env file.")
# Remove quotes if present (sometimes .env files have quotes around values)
mongodb_uri = mongodb_uri.strip().strip('"').strip("'")
app.config["MONGO_URI"] = mongodb_uri
# PyMongo is a Flask extension that makes it easy to use MongoDB
mongo = PyMongo(app)

# ------------------------------
# ENSURE REQUIRED COLLECTIONS EXIST
# ------------------------------
# Initialize collections and seed sample documents at application startup.
try:
    with app.app_context():
        db = mongo.db

        # Create collections if they do not exist
        for collection_name in ["publishers", "reviews", "reservations", "password_reset_tokens"]:
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
except Exception as e:
    pass  # MongoDB connection failed; skipping database initialization

# Register application blueprints
# Blueprints organize routes into separate files for better code organization
# pages_bp: Contains routes that render HTML pages (e.g., /all-books, /my-books)
# api_bp: Contains API routes that return JSON data (e.g., /api/books, /api/loans)
# When a user visits a URL, Flask checks these blueprints to find the matching route
app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)

# Run the Flask development server
# This starts the web server so users can access the application
if __name__ == "__main__":
    import os
    # Get port number from environment variable, default to 5001
    port = int(os.getenv("PORT", 5001))
    try:
        # Start the server in debug mode (auto-reloads on code changes)
        # The app will be accessible at http://127.0.0.1:5001
        app.run(debug=True, port=port)
    except OSError:
        # If port 5001 is already in use, try the next port (5002)
        # This prevents errors when the port is busy
        app.run(debug=True, port=port + 1)