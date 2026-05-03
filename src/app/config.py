import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask core ────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-ganti-di-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.getenv("SESSION_LIFETIME_HOURS", "8"))
    )

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

    # Google OAuth 2.0 (isi dari Google Cloud Console > OAuth client)
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_OAUTH_AUTH_URL = os.getenv(
        "GOOGLE_OAUTH_AUTH_URL",
        "https://accounts.google.com/o/oauth2/v2/auth",
    )
    GOOGLE_OAUTH_TOKEN_URL = os.getenv(
        "GOOGLE_OAUTH_TOKEN_URL",
        "https://oauth2.googleapis.com/token",
    )
    GOOGLE_OAUTH_USERINFO_URL = os.getenv(
        "GOOGLE_OAUTH_USERINFO_URL",
        "https://openidconnect.googleapis.com/v1/userinfo",
    )
    GOOGLE_OAUTH_SCOPES = os.getenv("GOOGLE_OAUTH_SCOPES", "openid email profile")
    GOOGLE_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv("GOOGLE_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
