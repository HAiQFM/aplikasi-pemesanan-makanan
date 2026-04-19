from app.models import db


class OrderItem(db.Model):
    """
    Tabel: order_items
    Menyimpan item individual dalam setiap pesanan (relasi one-to-many ke orders).
    Data menu didenormalisasi (menu_name, unit_price) agar riwayat pesanan tidak
    berubah jika admin mengedit harga menu di kemudian hari.

    Contoh SQL yang dihasilkan SQLAlchemy:
        CREATE TABLE order_items (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            order_id    INT NOT NULL,
            menu_name   VARCHAR(120) NOT NULL,
            quantity    INT NOT NULL DEFAULT 1,
            unit_price  DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            details     JSON,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            INDEX ix_order_items_order_id (order_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True
    )

    # Nama menu saat checkout (denormalized — tidak berubah walau menu diedit)
    menu_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    # Harga satuan saat checkout (snapshot)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Detail tambahan (misal: pilihan sambal) disimpan sebagai JSON Array
    # Contoh: [{"label": "Sambal", "value": "Sambal Matah"}]
    details = db.Column(db.JSON, nullable=True)

    # Relasi balik ke Order
    order = db.relationship("Order", back_populates="items")

    # ── Serialisasi ───────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Format dict yang kompatibel dengan template dan order_store lama."""
        return {
            "name": self.menu_name,
            "qty": self.quantity,
            "price": int(self.unit_price or 0),
            "details": self.details or [],
        }

    def __repr__(self) -> str:
        return f"<OrderItem order_id={self.order_id} menu={self.menu_name} qty={self.quantity}>"
