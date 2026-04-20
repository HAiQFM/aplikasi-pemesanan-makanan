import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def app():
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file.name}"
    os.environ["ADMIN_EMAIL"] = "admin@test.local"
    os.environ["ADMIN_PASSWORD"] = "Admin@Secure123"

    from app import create_app
    from app.models import Category, Ingredient, Menu, User, db

    flask_app = create_app()
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with flask_app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(name="Admin", email="admin@test.local", role="admin")
        admin.set_password("Admin@Secure123")
        customer = User(name="Firas User", email="firas@mail.com", role="customer")
        customer.set_password("secret123")
        category = Category(name="Paket Ayam", description="Menu ayam")
        menu = Menu(
            name="Nasi Ayam Geprek",
            category=category,
            price=13000,
            description="Pedas nikmat",
            is_available=True,
        )
        ingredient = Ingredient(
            name="Dada Ayam",
            unit="kg",
            current_stock=2,
            minimum_stock=5,
            note="Untuk ayam geprek",
        )

        db.session.add_all([admin, customer, category, menu, ingredient])
        db.session.commit()

    yield flask_app

    try:
        os.unlink(db_file.name)
    except OSError:
        pass


@pytest.fixture
def client(app):
    return app.test_client()
