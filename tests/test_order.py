import io


def login_customer(client):
    return client.post(
        "/auth/login",
        data={"email": "firas@mail.com", "password": "secret123"},
    )


def test_checkout_requires_login(client):
    response = client.get("/order/checkout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_checkout_page_shows_logged_in_name_without_input(client):
    login_customer(client)
    response = client.get("/order/checkout")
    assert response.status_code == 200
    assert b"Nama Pemesan" in response.data
    assert b"Firas User" in response.data
    assert b'name="customer_name"' not in response.data


def test_checkout_qris_creates_order_with_uploaded_proof(client, app):
    from app.models import Order

    login_customer(client)
    response = client.post(
        "/order/checkout",
        data={
            "address": "Jalan Mawar 123",
            "payment_method": "qris",
            "order_total": "13000",
            "checkout_items": '[{"name":"Nasi Ayam Geprek","qty":1,"price":13000,"details":[]}]',
            "payment_proof": (io.BytesIO(b"fake-image"), "bukti.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/order/success")

    with app.app_context():
        order = Order.query.first()
        assert order is not None
        assert order.customer_name == "Firas User"
        assert order.payment_method == "qris"
        assert order.payment_proof_path is not None


def test_success_page_resets_browser_cart_after_checkout(client):
    login_customer(client)
    response = client.post(
        "/order/checkout",
        data={
            "address": "Jalan Mawar 123",
            "payment_method": "cash",
            "order_total": "13000",
            "checkout_items": '[{"name":"Nasi Ayam Geprek","qty":1,"price":13000,"details":[]}]',
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b'localStorage.removeItem("foodhall_cart")' in response.data
    assert b'localStorage.removeItem("foodhall_promo_code")' in response.data


def test_order_history_page_loads_after_login(client):
    login_customer(client)
    response = client.get("/order/history")
    assert response.status_code == 200


def test_admin_ingredients_page_loads(client):
    client.post(
        "/auth/login",
        data={"email": "admin@test.local", "password": "Admin@Secure123"},
    )
    response = client.get("/admin/ingredients")
    assert response.status_code == 200
    assert b"Stok Bahan Baku" in response.data
    assert b"Dada Ayam" in response.data


def test_create_order_clears_database_cart_for_user(app):
    from app.models import Cart, Menu, User, db
    from app.services.order_store import create_order

    with app.app_context():
        user = User.query.filter_by(email="firas@mail.com").first()
        menu = Menu.query.filter_by(name="Nasi Ayam Geprek").first()
        db.session.add(Cart(user_id=user.id, menu_id=menu.id, quantity=2))
        db.session.commit()

        create_order(
            customer_name="Firas User",
            customer_email="firas@mail.com",
            address="Jalan Mawar 123",
            payment_method="cash",
            total_amount=26000,
            items=[
                {
                    "name": "Nasi Ayam Geprek",
                    "qty": 2,
                    "price": 13000,
                    "details": [],
                }
            ],
            user_id=user.id,
        )

        assert Cart.query.filter_by(user_id=user.id).count() == 0


def test_bom_decomposition_handles_nested_chicken_and_sambal():
    from app.services.inventory import build_deduction_list

    rows = build_deduction_list(
        [
            {
                "name": "Nasi Ayam Geprek",
                "qty": 2,
                "price": 13000,
                "details": [{"label": "Sambal", "value": "Sambal Matah"}],
            }
        ]
    )
    by_name = {row["ingredient_name"]: row for row in rows}

    assert by_name["Beras"]["quantity_deducted"] == 400
    assert by_name["Ayam Potong"]["quantity_deducted"] == 2
    assert by_name["Tepung Bumbu"]["quantity_deducted"] == 100
    assert by_name["Minyak Goreng"]["quantity_deducted"] == 60
    assert by_name["Bawang Merah"]["quantity_deducted"] == 30
    assert by_name["Cabai Rawit"]["quantity_deducted"] == 20
    assert by_name["Serai & Daun Jeruk"]["quantity_deducted"] == 10
    assert by_name["Minyak Kelapa"]["quantity_deducted"] == 20


def test_create_order_deducts_inventory_stock(app):
    from app.models import Ingredient, db
    from app.services.order_store import create_order

    with app.app_context():
        for name, unit, stock in [
            ("Beras", "g", 1000),
            ("Ayam Potong", "pcs", 10),
            ("Tepung Bumbu", "g", 500),
            ("Minyak Goreng", "ml", 300),
            ("Cabai Hijau", "g", 100),
            ("Tomat Hijau", "g", 100),
            ("Bawang Merah", "g", 100),
        ]:
            Ingredient.query.filter_by(name=name).delete()
            db.session.add(
                Ingredient(
                    name=name,
                    unit=unit,
                    current_stock=stock,
                    minimum_stock=0,
                )
            )

        db.session.commit()

        order = create_order(
            customer_name="Firas User",
            customer_email="firas@mail.com",
            address="Jalan Mawar 123",
            payment_method="cash",
            total_amount=26000,
            items=[
                {
                    "name": "Nasi Ayam Geprek",
                    "qty": 2,
                    "price": 13000,
                    "details": [{"label": "Sambal", "value": "Sambal Ijo"}],
                }
            ],
            user_id=None,
        )

        beras = Ingredient.query.filter_by(name="Beras").first()
        ayam = Ingredient.query.filter_by(name="Ayam Potong").first()
        bawang = Ingredient.query.filter_by(name="Bawang Merah").first()

        assert order["inventory_deductions"]
        assert float(beras.current_stock) == 600
        assert float(ayam.current_stock) == 8
        assert float(bawang.current_stock) == 90


def test_inventory_deduction_converts_bom_units_to_stock_units(app):
    from app.models import Ingredient, db
    from app.services.inventory import deduct_inventory_for_items

    with app.app_context():
        for name, unit, stock in [
            ("Beras", "kg", 2),
            ("Minyak Goreng", "liter", 1),
            ("Ayam Potong", "pcs", 5),
            ("Tepung Bumbu", "g", 500),
        ]:
            Ingredient.query.filter_by(name=name).delete()
            db.session.add(
                Ingredient(
                    name=name,
                    unit=unit,
                    current_stock=stock,
                    minimum_stock=0,
                )
            )
        db.session.commit()

        rows = deduct_inventory_for_items(
            [{"name": "Nasi Ayam Geprek", "qty": 1, "price": 13000, "details": []}]
        )

        by_name = {row["ingredient_name"]: row for row in rows}
        beras = Ingredient.query.filter_by(name="Beras").first()
        minyak = Ingredient.query.filter_by(name="Minyak Goreng").first()

        assert by_name["Beras"]["unit"] == "kg"
        assert by_name["Beras"]["quantity_deducted"] == 0.2
        assert by_name["Minyak Goreng"]["unit"] == "liter"
        assert by_name["Minyak Goreng"]["quantity_deducted"] == 0.03
        assert float(beras.current_stock) == 1.8
        assert float(minyak.current_stock) == 0.97


def test_admin_orders_page_shows_inventory_deductions(client, app):
    from app.models import Ingredient, db
    from app.services.order_store import create_order

    with app.app_context():
        for name, unit, stock in [
            ("Beras", "g", 1000),
            ("Ayam Potong", "pcs", 10),
            ("Tepung Bumbu", "g", 500),
            ("Minyak Goreng", "ml", 300),
        ]:
            Ingredient.query.filter_by(name=name).delete()
            db.session.add(
                Ingredient(
                    name=name,
                    unit=unit,
                    current_stock=stock,
                    minimum_stock=0,
                )
            )
        db.session.commit()

        create_order(
            customer_name="Firas User",
            customer_email="firas@mail.com",
            address="Jalan Mawar 123",
            payment_method="cash",
            total_amount=13000,
            items=[
                {
                    "name": "Nasi Ayam Geprek",
                    "qty": 1,
                    "price": 13000,
                    "details": [],
                }
            ],
            user_id=None,
        )

    client.post(
        "/auth/login",
        data={"email": "admin@test.local", "password": "Admin@Secure123"},
    )
    response = client.get("/admin/orders")

    assert response.status_code == 200
    assert b"Menu Dipesan" in response.data
    assert b"1x Nasi Ayam Geprek" in response.data
    assert b"Deduksi Stok" in response.data
    assert b"Beras" in response.data
    assert b"200,00" in response.data
