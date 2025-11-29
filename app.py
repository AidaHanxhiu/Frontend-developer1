from flask import Flask
from pymongo import MongoClient
from routes.__init__ import all_blueprints

def get_db():
    client = MongoClient('mongodb+srv://anila:anila12345@cluster0.x8mua2a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')

    db = client["library_system"]
    return db

def create_app():
    app = Flask(__name__)
    app.config["DB"] = get_db()

    for bp in all_blueprints:
        app.register_blueprint(bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

