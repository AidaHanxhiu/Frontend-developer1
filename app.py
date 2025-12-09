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

# register blueprints
app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)

# run app
if __name__ == "__main__":
    app.run(debug=True)
