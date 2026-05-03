def test_login_page_loads(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_register_page_loads(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_login_post_redirects_to_home(client):
    response = client.post(
        "/auth/login",
        data={"email": "firas@mail.com", "password": "secret123"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


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


def test_google_login_redirects_to_home_when_not_configured(client):
    response = client.get("/auth/google/login")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_google_login_redirects_to_google_when_configured(app, client):
    app.config.update(
        GOOGLE_CLIENT_ID="client-test.apps.googleusercontent.com",
        GOOGLE_CLIENT_SECRET="secret-test",
    )

    response = client.get("/auth/google/login")
    assert response.status_code == 302
    assert response.headers["Location"].startswith(
        "https://accounts.google.com/o/oauth2/v2/auth"
    )
    assert "client-test.apps.googleusercontent.com" in response.headers["Location"]

    with client.session_transaction() as auth_session:
        assert auth_session["google_oauth_state"]


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
