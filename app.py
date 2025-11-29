from flask import Flask
from routes import all_blueprints
from pymongo import MongoClient

# -------------------------------
# DATABASE CONNECTION (MongoDB)
# -------------------------------
def get_db():
    # TODO: replace this with your real MongoDB Atlas connection string
    client = MongoClient("YOUR_MONGODB_ATLAS_URI")

    # Choose the database name
    db = client["library_system"]

    return db


# -------------------------------
# FLASK APP FACTORY
# -------------------------------
def create_app():
    app = Flask(__name__)

    # Make get_db available inside the app context if needed
    app.get_db = get_db

    # REGISTER ALL BLUEPRINTS
    for bp in all_blueprints:
        app.register_blueprint(bp)

    return app


# -------------------------------
# RUNNING THE APP
# -------------------------------
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
