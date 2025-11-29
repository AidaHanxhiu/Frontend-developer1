from pymongo import MongoClient

def get_db():
    client = MongoClient("YOUR_MONGODB_ATLAS_URI")
    db = client["library_system"]
    return db


from flask import Flask
from routes import all_blueprints


def create_app():
    app = Flask(__name__)

    # Register blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
