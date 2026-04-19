"""
app/__init__.py — Application factory.

Perubahan dari versi sebelumnya:
  - Flask-Migrate diregistrasi untuk manajemen skema DB via CLI
  - db.create_all() dipanggil otomatis saat dev (auto-buat tabel jika belum ada)
  - Akun admin di-seed dari ADMIN_EMAIL / ADMIN_PASSWORD di .env
"""

from flask import Flask
from flask_migrate import Migrate

from app.config import Config
from app.models import db
from app.routes import register_blueprints

# Instance Migrate global agar CLI flask db init/migrate/upgrade bisa berjalan
migrate = Migrate()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Init ekstensi ─────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)  # aktifkan: flask db init / migrate / upgrade

    @app.after_request
    def add_no_store_headers(response):
        if response.mimetype == "text/html":
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    register_blueprints(app)

    # ── Bootstrap DB (buat tabel + seed admin) ────────────────────────────────
    # Untuk production: hapus blok ini dan gunakan `flask db upgrade` saja.
    with app.app_context():
        _bootstrap_database(app)

    return app


def _bootstrap_database(app: Flask) -> None:
    """
    Buat tabel yang belum ada dan seed akun admin pertama kali.
    Aman dijalankan berulang — tidak menimpa data yang sudah ada.
    """
    try:
        db.create_all()
        _seed_admin_user(app)
    except Exception as exc:
        # Jangan crash jika DB belum bisa dijangkau (misal: Docker belum ready)
        app.logger.warning(f"[bootstrap] Gagal inisialisasi DB: {exc}")


def _seed_admin_user(app: Flask) -> None:
    """
    Buat akun admin dari .env jika belum ada di tabel `users`.
    Variabel: ADMIN_EMAIL, ADMIN_PASSWORD
    """
    # Import di dalam fungsi untuk menghindari circular import
    from app.models import User

    admin_email = app.config.get("ADMIN_EMAIL", "").strip().lower()
    admin_password = app.config.get("ADMIN_PASSWORD", "")

    if not admin_email or not admin_password:
        return  # config tidak ada — lewati

    if User.query.filter_by(email=admin_email).first():
        return  # sudah ada — tidak perlu dibuat ulang

    admin = User(name="Admin", email=admin_email, role="admin")
    admin.set_password(admin_password)  # werkzeug pbkdf2:sha256
    db.session.add(admin)
    db.session.commit()
    app.logger.info(f"[bootstrap] Akun admin '{admin_email}' berhasil dibuat.")
