# routes/__init__.py

from .routes_pages import pages
from .routes_api import api

all_blueprints = [
    pages,
    api
]
