from datetime import datetime

from app.models import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    menus = db.relationship("Menu", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
