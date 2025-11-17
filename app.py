from flask import Flask
from routes import all_blueprints

def create_app():
    app = Flask(__name__)

    # Register all blueprints (all routes from routes folder)
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
