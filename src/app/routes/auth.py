"""
routes/auth.py — Autentikasi berbasis database MySQL.

Perubahan dari versi session-only:
  - Registrasi: menyimpan User ke tabel `users` dengan password ter-hash
  - Login customer: verifikasi terhadap password_hash di DB
  - Login admin: verifikasi terhadap akun User role='admin' di DB
  - Tidak ada lagi kredensial hardcoded di kode sumber
"""

import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _reset_auth_session() -> None:
    """Bersihkan session saat logout."""
    session.clear()


class GoogleOAuthError(RuntimeError):
    """Error yang aman ditampilkan sebagai flash message untuk OAuth Google."""


def _set_auth_session(user: User) -> None:
    session["is_logged_in"] = True
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.name
    session["user_role"] = user.role


def _render_login_template():
    return render_template(
        "auth/login.html",
        google_client_id=current_app.config.get("GOOGLE_CLIENT_ID", ""),
        google_login_enabled=_google_oauth_configured(),
        google_csrf_token=_get_google_csrf_token(),
    )


def _google_oauth_configured() -> bool:
    return bool(current_app.config.get("GOOGLE_CLIENT_ID"))


def _google_redirect_oauth_configured() -> bool:
    return bool(
        current_app.config.get("GOOGLE_CLIENT_ID")
        and current_app.config.get("GOOGLE_CLIENT_SECRET")
    )


def _get_google_csrf_token() -> str:
    token = session.get("google_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["google_csrf_token"] = token
    return token


def _origin_allowed() -> bool:
    origin = request.headers.get("Origin")
    if not origin:
        return True

    allowed_origins = {
        value.strip().rstrip("/")
        for value in current_app.config.get("GOOGLE_ALLOWED_ORIGINS", [])
        if value.strip()
    }
    if not allowed_origins:
        allowed_origins.add(request.host_url.rstrip("/"))

    return origin.rstrip("/") in allowed_origins


def _google_redirect_uri() -> str:
    return url_for("auth.google_callback", _external=True)


def _read_json_response(response) -> dict:
    return json.loads(response.read().decode("utf-8"))


def _request_google_json(
    url: str,
    *,
    data: dict = None,
    access_token: str = "",
) -> dict:
    headers = {"Accept": "application/json"}
    body = None

    if data is not None:
        body = urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    try:
        with urlopen(Request(url, data=body, headers=headers), timeout=10) as response:
            return _read_json_response(response)
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        current_app.logger.warning("[google-oauth] HTTP error %s: %s", exc.code, details)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        current_app.logger.warning("[google-oauth] Request failed: %s", exc)

    raise GoogleOAuthError("Login Google gagal diproses. Silakan coba lagi.")


def _exchange_google_code(code: str) -> dict:
    return _request_google_json(
        current_app.config["GOOGLE_OAUTH_TOKEN_URL"],
        data={
            "code": code,
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": _google_redirect_uri(),
            "grant_type": "authorization_code",
        },
    )


def _fetch_google_profile(access_token: str) -> dict:
    if not access_token:
        raise GoogleOAuthError("Token Google tidak valid.")
    return _request_google_json(
        current_app.config["GOOGLE_OAUTH_USERINFO_URL"],
        access_token=access_token,
    )


def _find_or_create_google_user(profile: dict) -> User:
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip() or email.split("@")[0]

    if not email:
        raise GoogleOAuthError("Akun Google tidak mengirim alamat email.")

    if profile.get("email_verified") is False:
        raise GoogleOAuthError("Email Google belum terverifikasi.")

    user = User.query.filter_by(email=email).first()
    if user:
        if not user.is_active:
            raise GoogleOAuthError("Akun Anda sedang dinonaktifkan.")
        return user

    user = User(name=name, email=email, role="customer")
    user.set_password(secrets.token_urlsafe(32))
    db.session.add(user)
    db.session.commit()
    return user


def _verify_google_id_token(credential: str) -> dict:
    if not credential:
        raise GoogleOAuthError("Token Google tidak ditemukan.")

    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise GoogleOAuthError("Login Google belum dikonfigurasi.")

    try:
        payload = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except ValueError as exc:
        current_app.logger.warning("[google-gis] ID token verification failed: %s", exc)
        raise GoogleOAuthError("Token Google tidak valid.") from exc

    issuer = payload.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        current_app.logger.warning("[google-gis] Invalid issuer: %s", issuer)
        raise GoogleOAuthError("Issuer token Google tidak valid.")

    if payload.get("aud") != client_id:
        current_app.logger.warning("[google-gis] Invalid audience: %s", payload.get("aud"))
        raise GoogleOAuthError("Audience token Google tidak sesuai.")

    return payload


# ── REGISTER ──────────────────────────────────────────────────────────────────


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    CREATE — Simpan user baru ke tabel `users`.

    Sebelumnya: session["users"][email] = name  (hilang saat browser tutup)
    Sekarang  : INSERT INTO users (name, email, password_hash, role) VALUES (...)
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Validasi input
        if not name or not email or not password:
            flash("Semua field wajib diisi.", "error")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Konfirmasi password tidak cocok.", "error")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password minimal 8 karakter.", "error")
            return render_template("auth/register.html")

        # Cek duplikat email di DB
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email sudah terdaftar, silakan login.", "error")
            return render_template("auth/register.html")

        # Buat user baru dengan password ter-hash (pbkdf2:sha256)
        new_user = User(name=name, email=email, role="customer")
        new_user.set_password(password)  # werkzeug.security.generate_password_hash
        db.session.add(new_user)
        db.session.commit()

        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ── LOGIN ─────────────────────────────────────────────────────────────────────


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    READ — Verifikasi kredensial terhadap tabel `users`.

    Sebelumnya: cek email di session["users"], admin hardcoded
    Sekarang  : SELECT * FROM users WHERE email = ? → check_password_hash
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email dan password wajib diisi.", "error")
            return _render_login_template()

        # Cari user di DB
        user = User.query.filter_by(email=email, is_active=True).first()

        if user is None:
            flash("Email tidak terdaftar atau akun dinonaktifkan.", "error")
            return _render_login_template()

        # Verifikasi password menggunakan werkzeug.security.check_password_hash
        if not user.check_password(password):
            flash("Password salah.", "error")
            return _render_login_template()

        _set_auth_session(user)

        if user.role == "admin":
            flash("Login admin berhasil.", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Login berhasil.", "success")
        return redirect(url_for("main.index"))

    return _render_login_template()


@auth_bp.route("/google/login")
def google_login():
    if not _google_redirect_oauth_configured():
        flash("Login Google belum dikonfigurasi.", "error")
        return redirect(url_for("main.index"))

    state = secrets.token_urlsafe(32)
    session["google_oauth_state"] = state

    params = {
        "client_id": current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri": _google_redirect_uri(),
        "response_type": "code",
        "scope": current_app.config["GOOGLE_OAUTH_SCOPES"],
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
        "include_granted_scopes": "true",
    }
    return redirect(f"{current_app.config['GOOGLE_OAUTH_AUTH_URL']}?{urlencode(params)}")


@auth_bp.route("/google/callback")
def google_callback():
    expected_state = session.pop("google_oauth_state", "")
    received_state = request.args.get("state", "")

    if not expected_state or expected_state != received_state:
        flash("Sesi login Google tidak valid. Silakan coba lagi.", "error")
        return redirect(url_for("main.index"))

    if request.args.get("error"):
        flash("Login Google dibatalkan atau ditolak.", "error")
        return redirect(url_for("main.index"))

    code = request.args.get("code", "")
    if not code:
        flash("Kode otorisasi Google tidak ditemukan.", "error")
        return redirect(url_for("main.index"))

    try:
        token = _exchange_google_code(code)
        profile = _fetch_google_profile(token.get("access_token", ""))
        user = _find_or_create_google_user(profile)
    except GoogleOAuthError as exc:
        flash(str(exc), "error")
        return redirect(url_for("main.index"))

    _set_auth_session(user)
    flash("Login Google berhasil.", "success")
    return redirect(url_for("main.index"))


# ── LOGOUT ────────────────────────────────────────────────────────────────────


@auth_bp.route("/google/credential", methods=["POST"])
def google_credential_login():
    if not _google_oauth_configured():
        return jsonify({"message": "Login Google belum dikonfigurasi."}), 503

    if not _origin_allowed():
        return jsonify({"message": "Origin tidak diizinkan."}), 403

    expected_csrf = session.get("google_csrf_token", "")
    received_csrf = request.headers.get("X-CSRF-Token", "")
    if not expected_csrf or not secrets.compare_digest(expected_csrf, received_csrf):
        return jsonify({"message": "Sesi login Google tidak valid."}), 403

    data = request.get_json(silent=True) or {}
    credential = data.get("credential", "")

    try:
        payload = _verify_google_id_token(credential)
        user = _find_or_create_google_user(payload)
    except GoogleOAuthError as exc:
        return jsonify({"message": str(exc)}), 401

    session.pop("google_csrf_token", None)
    _set_auth_session(user)
    session.permanent = True

    return jsonify(
        {
            "message": "Login Google berhasil.",
            "redirect_url": url_for("main.index"),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            },
        }
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    _reset_auth_session()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout-admin", methods=["POST"])
def logout_admin():
    _reset_auth_session()
    flash("Admin logout berhasil.", "info")
    return redirect(url_for("main.index"))
