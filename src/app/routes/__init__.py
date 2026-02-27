from flask import Blueprint, Flask, render_template

from app.routes.auth import auth_bp
from app.routes.cart import cart_bp
from app.routes.order import order_bp

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
