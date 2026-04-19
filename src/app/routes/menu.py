"""
routes/menu.py — Endpoint daftar menu dan detail.

Perubahan dari versi hardcoded:
  - Tampilkan menu dari tabel `menus` yang di-join dengan `categories`
  - Fallback ke data hardcoded jika tabel kosong (untuk dev awal tanpa seeder)
  - Admin dapat mengelola menu melalui routes/admin.py
"""

import re
from pathlib import Path

from flask import Blueprint, current_app, render_template

from app.models import Category, Menu

menu_bp = Blueprint("menu", __name__, url_prefix="/menu")


def _normalize_image_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def _resolve_image_filename(item_name: str, fallback_name: str) -> str:
    """Cari file gambar di static/images yang cocok dengan nama menu."""
    images_dir = Path(current_app.static_folder) / "images"
    candidates = []
    for raw_value in [fallback_name, item_name]:
        normalized = _normalize_image_key(raw_value)
        if normalized:
            candidates.append(normalized)

    if images_dir.exists():
        for image_path in images_dir.iterdir():
            if not image_path.is_file():
                continue
            normalized_file_name = _normalize_image_key(image_path.stem)
            if normalized_file_name in candidates:
                return image_path.name

    return fallback_name or "logo.png"


def _menu_model_to_dict(menu: Menu) -> dict:
    """
    Konversi objek Menu SQLAlchemy ke dict yang kompatibel dengan template.
    (template menggunakan key: name, category, price, price_value, desc, image, id)
    """
    price_value = int(menu.price or 0)
    return {
        "id": menu.id,
        "name": menu.name,
        "category": menu.category.name if menu.category else "",
        "price": f"Rp {price_value:,.0f}".replace(",", "."),
        "price_value": price_value,
        "desc": menu.description or "",
        "image": _resolve_image_filename(menu.name, menu.image_url or "logo.png"),
        "is_available": menu.is_available,
    }


# ── Data hardcoded sebagai fallback jika DB kosong ───────────────────────────

_HARDCODED_MENU = [
    {
        "name": "Nasi Ayam Geprek",
        "category": "Paket Ayam",
        "price": "Rp 13.000",
        "price_value": 13000,
        "desc": "Ayam geprek crispy dengan nasi hangat.",
        "image": "nasi ayam penyet.jfif",
    },
    {
        "name": "Nasi Ayam Bakar",
        "category": "Paket Ayam",
        "price": "Rp 13.000",
        "price_value": 13000,
        "desc": "Ayam bakar bumbu manis gurih dengan nasi.",
        "image": "nasi ayam bakar.jfif",
    },
    {
        "name": "Nasi Ayam Penyet",
        "category": "Paket Ayam",
        "price": "Rp 13.000",
        "price_value": 13000,
        "desc": "Ayam penyet empuk dengan lalapan segar.",
        "image": "nasi ayam penyet.jfif",
    },
]

_HARDCODED_DRINKS = [
    {
        "name": "Tea Jus",
        "category": "Minuman",
        "price": "Rp 3.000",
        "price_value": 3000,
        "desc": "Teh manis dingin khas warung.",
        "image": "logo.png",
    },
    {
        "name": "Es Teh Manis",
        "category": "Minuman",
        "price": "Rp 5.000",
        "price_value": 5000,
        "desc": "Teh dingin dengan gula sesuai selera.",
        "image": "es teh manis.jfif",
    },
    {
        "name": "Jus Mangga",
        "category": "Minuman",
        "price": "Rp 10.000",
        "price_value": 10000,
        "desc": "Jus Mangga sehat, bisa request rasa.",
        "image": "logo.png",
    },
    {
        "name": "Jus Alpukat",
        "category": "Minuman",
        "price": "Rp 12.000",
        "price_value": 12000,
        "desc": "Jus alpukat creamy ala warung.",
        "image": "logo.png",
    },
    {
        "name": "Jus Jambu",
        "category": "Minuman",
        "price": "Rp 10.000",
        "price_value": 10000,
        "desc": "Jus jambu segar dengan rasa manis alami.",
        "image": "jus jambu.jfif",
    },
    {
        "name": "Jus Jeruk",
        "category": "Minuman",
        "price": "Rp 8.000",
        "price_value": 8000,
        "desc": "Jus jeruk manis segar.",
        "image": "logo.png",
    },
    {
        "name": "Kopi",
        "category": "Minuman",
        "price": "Rp 5.000",
        "price_value": 5000,
        "desc": "Kopi hitam panas khas warung.",
        "image": "logo.png",
    },
    {
        "name": "Air Mineral",
        "category": "Minuman",
        "price": "Rp 4.000",
        "price_value": 4000,
        "desc": "Air mineral dingin untuk pendamping menu utama.",
        "image": "logo.png",
    },
]


@menu_bp.route("/")
def index():
    """
    READ — Ambil menu dari DB, fallback ke data hardcoded jika DB kosong.

    Sebelumnya: list Python hardcoded di kode ini
    Sekarang  : SELECT menus.*, categories.name FROM menus JOIN categories ...
    """
    sambal_options = ["Sambal Merah", "Sambal Ijo", "Sambal Matah"]

    # Coba ambil dari DB
    try:
        all_menus = (
            Menu.query.filter_by(is_available=True)
            .join(Category)
            .order_by(Category.name, Menu.name)
            .all()
        )
    except Exception:
        # Fallback jika tabel belum ada (sebelum migrasi dijalankan)
        all_menus = []

    if all_menus:
        # Split berdasarkan kategori
        menu_items = [
            _menu_model_to_dict(m)
            for m in all_menus
            if m.category and m.category.name != "Minuman"
        ]
        drink_items = [
            _menu_model_to_dict(m)
            for m in all_menus
            if m.category and m.category.name == "Minuman"
        ]
    else:
        # Fallback hardcoded (untuk development awal sebelum seed)
        menu_items = _HARDCODED_MENU
        drink_items = _HARDCODED_DRINKS

    return render_template(
        "menu/index.html",
        menu_items=menu_items,
        drink_items=drink_items,
        sambal_options=sambal_options,
    )


@menu_bp.route("/<int:menu_id>", methods=["GET"])
def detail(menu_id: int):
    """READ — Detail satu menu berdasarkan ID."""
    menu = Menu.query.get_or_404(menu_id)
    return render_template("menu/detail.html", menu=_menu_model_to_dict(menu))
