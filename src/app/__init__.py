from flask import Flask

from app.config import Config
from app.models import db
from app.routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    register_blueprints(app)

    return app
