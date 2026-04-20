def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_login_post_redirects_to_order_history(client):
    response = client.post(
        "/auth/login",
        data={"email": "firas@mail.com", "password": "secret123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/order/history")


def test_register_post_redirects_to_login(client):
    response = client.post(
        "/auth/register",
        data={
            "name": "User Baru",
            "email": "baru@mail.com",
            "password": "secret123",
            "confirm_password": "secret123",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_admin_login_redirects_to_dashboard(client):
    response = client.post(
        "/auth/login",
        data={"email": "admin@test.local", "password": "Admin@Secure123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")


def test_logout_redirects_to_login(client):
    response = client.post("/auth/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_non_admin_cannot_access_admin_pages(client):
    client.post(
        "/auth/login",
        data={"email": "firas@mail.com", "password": "secret123"},
    )
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_admin_dashboard_shows_low_stock_notification(client):
    client.post(
        "/auth/login",
        data={"email": "admin@test.local", "password": "Admin@Secure123"},
    )
    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"Notifikasi Stok Minimum" in response.data
    assert b"Dada Ayam" in response.data
