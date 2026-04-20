from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Re-export semua model agar bisa diimport langsung:
#   from app.models import User, Order, OrderItem, Menu, Category, Cart
from app.models.user import User  # noqa: E402,F401
from app.models.category import Category  # noqa: E402,F401
from app.models.menu import Menu  # noqa: E402,F401
from app.models.ingredient import Ingredient  # noqa: E402,F401
from app.models.cart import Cart  # noqa: E402,F401
from app.models.order import Order  # noqa: E402,F401
from app.models.order_item import OrderItem  # noqa: E402,F401
