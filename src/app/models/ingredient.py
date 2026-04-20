from datetime import datetime

from app.models import db


class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    unit = db.Column(db.String(30), nullable=False, default="pcs")
    current_stock = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    minimum_stock = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    note = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    @property
    def stock_value(self) -> float:
        return float(self.current_stock or 0)

    @property
    def minimum_value(self) -> float:
        return float(self.minimum_stock or 0)

    @property
    def is_below_minimum(self) -> bool:
        return self.stock_value <= self.minimum_value

    def __repr__(self) -> str:
        return f"<Ingredient {self.name} stock={self.current_stock}>"
