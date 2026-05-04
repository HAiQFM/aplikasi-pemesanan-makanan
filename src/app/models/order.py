from datetime import datetime

from app.models import db


class Order(db.Model):
    """
    Tabel: orders
    Menyimpan setiap transaksi pesanan. user_id bersifat opsional (NULL untuk tamu/guest).
    Data pelanggan (customer_name, customer_email) didenormalisasi agar riwayat tidak
    berubah jika pengguna mengedit profilnya.
    """

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    # FK ke users.id, nullable agar guest (tanpa akun) bisa memesan
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )

    # Data pelanggan didenormalisasi (snapshot saat checkout)
    customer_name = db.Column(db.String(120), nullable=False, default="")
    customer_email = db.Column(db.String(255), nullable=False, default="", index=True)
    address = db.Column(db.Text, nullable=True)

    # Pembayaran
    payment_method = db.Column(db.String(50), nullable=True)  # cash|transfer|ewallet
    payment_proof_path = db.Column(
        db.String(255), nullable=True
    )  # path file bukti bayar
    payment_verification = db.Column(
        db.String(20),
        nullable=False,
        default="pending",  # pending|verified
    )

    # Total dan status
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(
        db.String(50),
        nullable=False,
        default="Menunggu Pembayaran",
        # Nilai valid: Menunggu Pembayaran | Sedang Dimasak | Dalam Perjalanan | Selesai | Dibatalkan
    )
    inventory_deductions = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relasi
    user = db.relationship("User", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="select"
    )

    # ── Serialisasi ───────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Kembalikan representasi dict (format yang sama dengan order_store.py lama
        agar template tidak perlu diubah).
        """
        return {
            "id": self.id,
            "customer_name": self.customer_name or "",
            "customer_email": self.customer_email or "",
            "address": self.address or "",
            "payment_method": self.payment_method or "",
            "payment_proof_path": self.payment_proof_path,
            "payment_verification": self.payment_verification or "pending",
            "total_amount": int(self.total_amount or 0),
            "items": [item.to_dict() for item in self.items],
            "inventory_deductions": self.inventory_deductions or [],
            "status": self.status or "",
            "created_at": (
                self.created_at.isoformat(timespec="seconds") if self.created_at else ""
            ),
            "updated_at": (
                self.updated_at.isoformat(timespec="seconds") if self.updated_at else ""
            ),
        }

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status}>"
