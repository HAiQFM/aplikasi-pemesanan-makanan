from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.models import db


class User(db.Model):
    """
    Tabel: users
    Menyimpan data akun pelanggan dan admin.
    Password disimpan dalam bentuk hash (Werkzeug pbkdf2:sha256).
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    # Hash dihasilkan oleh werkzeug.security.generate_password_hash
    # JANGAN simpan plaintext password di sini
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relasi ke Cart dan Order (cascade delete)
    carts = db.relationship("Cart", back_populates="user", cascade="all, delete-orphan")
    orders = db.relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )

    # ── Password helpers ──────────────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash password menggunakan Werkzeug pbkdf2:sha256 dan simpan ke password_hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifikasi password terhadap hash yang tersimpan di DB."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
