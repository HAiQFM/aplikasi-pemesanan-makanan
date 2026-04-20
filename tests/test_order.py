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
