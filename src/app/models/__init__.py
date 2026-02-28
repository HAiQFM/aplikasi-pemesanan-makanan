from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Re-export model classes for easier imports: from app.models import User, Cart, Order
from app.models.category import Category  # noqa: E402,F401
from app.models.menu import Menu  # noqa: E402,F401
from app.models.cart import Cart  # noqa: E402,F401
from app.models.order import Order  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401
