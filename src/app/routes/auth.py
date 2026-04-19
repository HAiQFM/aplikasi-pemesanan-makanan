"""
routes/auth.py — Autentikasi berbasis database MySQL.

Perubahan dari versi session-only:
  - Registrasi: menyimpan User ke tabel `users` dengan password ter-hash
  - Login customer: verifikasi terhadap password_hash di DB
  - Login admin: verifikasi terhadap akun User role='admin' di DB
  - Tidak ada lagi kredensial hardcoded di kode sumber
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _reset_auth_session() -> None:
    """Bersihkan session saat logout."""
    session.clear()


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
            return render_template("auth/login.html")

        # Cari user di DB
        user = User.query.filter_by(email=email, is_active=True).first()

        if user is None:
            flash("Email tidak terdaftar atau akun dinonaktifkan.", "error")
            return render_template("auth/login.html")

        # Verifikasi password menggunakan werkzeug.security.check_password_hash
        if not user.check_password(password):
            flash("Password salah.", "error")
            return render_template("auth/login.html")

        # Set session
        session["is_logged_in"] = True
        session["user_id"] = user.id  # ← baru: simpan ID untuk FK pesanan
        session["user_email"] = user.email
        session["user_name"] = user.name
        session["user_role"] = user.role

        if user.role == "admin":
            flash("Login admin berhasil.", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Login berhasil.", "success")
        return redirect(url_for("order.history"))

    return render_template("auth/login.html")


# ── LOGOUT ────────────────────────────────────────────────────────────────────


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
