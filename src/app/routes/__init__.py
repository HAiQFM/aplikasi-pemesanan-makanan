from flask import Blueprint, Flask, render_template, session

from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.cart import cart_bp
from app.routes.menu import get_menu_sections, menu_bp
from app.routes.order import order_bp
from app.services.order_store import STATUS_LABELS, status_counts

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    user_email = session.get("user_email", "").strip().lower() if session.get("is_logged_in") else ""
    counts = status_counts(customer_email=user_email) if user_email else {label: 0 for label in STATUS_LABELS}
    menu_sections = get_menu_sections(randomize_home=True)
    return render_template(
        "index.html",
        status_counts=counts,
        status_total=sum(counts.values()),
        quick_menu_items=menu_sections["quick_menu_items"],
        slideshow_items=menu_sections["slideshow_items"],
    )


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
