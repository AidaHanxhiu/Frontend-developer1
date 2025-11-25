from flask import Flask
from routes import all_blueprints

def create_app():
    app = Flask(__name__)

    # REGISTER ALL BLUEPRINTS
    for bp in all_blueprints:
        app.register_blueprint(bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
