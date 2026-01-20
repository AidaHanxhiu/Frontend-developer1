# routes/__init__.py

from .routes_pages import pages_bp
from .routes_api import api_bp

all_blueprints = [
    pages_bp,
    api_bp
]