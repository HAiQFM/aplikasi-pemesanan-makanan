from datetime import datetime

from app.models import db


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    menu_id = db.Column(db.Integer, db.ForeignKey("menus.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="carts")
    menu = db.relationship("Menu", back_populates="carts")

    def __repr__(self) -> str:
        return f"<Cart user_id={self.user_id} menu_id={self.menu_id} qty={self.quantity}>"
