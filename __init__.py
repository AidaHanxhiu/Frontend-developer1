
from flask import Flask
from routes.routes_api import api_bp

def create_app():
    app = Flask(__name__)
    # ...existing code...

    # Register the API Blueprint
    app.register_blueprint(api_bp)

    return app