from flask import Flask
from config import Config
from db import init_app
from api import api_bp

def create_app():
    app = Flask(__name__)
    Config.init_app(app)
    init_app(app)
    app.register_blueprint(api_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)