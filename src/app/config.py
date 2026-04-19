import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask core ────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-ganti-di-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # ── SQLAlchemy / MySQL ────────────────────────────────────────────────────
    # Gunakan driver PyMySQL: mysql+pymysql://user:pass@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/pemesanan_makanan",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Pool settings agar koneksi tidak putus karena MySQL wait_timeout (default 8 jam)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,  # recycle koneksi setiap 280 detik
        "pool_pre_ping": True,  # cek koneksi sebelum dipakai (mencegah stale connection)
        "pool_size": 10,  # jumlah koneksi persistent dalam pool
        "max_overflow": 20,  # koneksi tambahan saat pool penuh
    }

    # ── Admin default (dibaca oleh seed script / auth bootstrap) ─────────────
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@Secure123")
