from flask import Flask
from flask_pymongo import PyMongo
from routes.routes_pages import pages_bp
from routes.routes_api import api_bp

app = Flask(__name__)
app.secret_key = "supersecret123"  # required for sessions

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
