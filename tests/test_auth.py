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


def test_google_credential_login_requires_csrf(app, client):
    app.config.update(GOOGLE_CLIENT_ID="client-test.apps.googleusercontent.com")

    response = client.post(
        "/auth/google/credential",
        json={"credential": "fake-token"},
    )

    assert response.status_code == 403


def test_google_credential_login_creates_session(app, client, monkeypatch):
    app.config.update(GOOGLE_CLIENT_ID="client-test.apps.googleusercontent.com")

    client.get("/auth/login")
    with client.session_transaction() as auth_session:
        csrf_token = auth_session["google_csrf_token"]

    def fake_verify_google_id_token(credential):
        assert credential == "valid-token"
        return {
            "iss": "https://accounts.google.com",
            "aud": "client-test.apps.googleusercontent.com",
            "sub": "google-user-1",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
        }

    from app.routes import auth

    monkeypatch.setattr(auth, "_verify_google_id_token", fake_verify_google_id_token)

    response = client.post(
        "/auth/google/credential",
        json={"credential": "valid-token"},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    assert response.json["redirect_url"] == "/"
    assert response.json["user"]["email"] == "google-user@example.com"

    with client.session_transaction() as auth_session:
        assert auth_session["is_logged_in"] is True
        assert auth_session["user_email"] == "google-user@example.com"


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
