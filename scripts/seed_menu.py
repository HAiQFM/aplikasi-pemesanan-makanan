"""
scripts/seed_menu.py — Seed data menu & kategori dari data hardcoded ke MySQL.

Jalankan SEKALI setelah database MySQL sudah dibuat:
    cd aplikasi-pemesanan-makanan
    python scripts/seed_menu.py

Aman dijalankan berulang — menggunakan INSERT OR IGNORE (get_or_create pattern).
"""

import sys
from pathlib import Path

# Tambahkan src/ ke Python path agar bisa import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import create_app
from app.models import Category, Menu, db

# ── Data master menu ──────────────────────────────────────────────────────────

CATEGORIES = [
    {"name": "Paket Ayam", "description": "Paket nasi dengan lauk ayam pilihan"},
    {"name": "Minuman", "description": "Minuman segar dan hangat"},
]

MENUS = [
    # ── Paket Ayam ──
    {
        "category": "Paket Ayam",
        "name": "Nasi Ayam Geprek",
        "description": "Ayam geprek crispy dengan nasi hangat.",
        "price": 13000,
        "image_url": "nasi ayam penyet.jfif",
        "is_available": True,
    },
    {
        "category": "Paket Ayam",
        "name": "Nasi Ayam Bakar",
        "description": "Ayam bakar bumbu manis gurih dengan nasi.",
        "price": 13000,
        "image_url": "nasi ayam bakar.jfif",
        "is_available": True,
    },
    {
        "category": "Paket Ayam",
        "name": "Nasi Ayam Penyet",
        "description": "Ayam penyet empuk dengan lalapan segar.",
        "price": 13000,
        "image_url": "nasi ayam penyet.jfif",
        "is_available": True,
    },
    # ── Minuman ──
    {
        "category": "Minuman",
        "name": "Tea Jus",
        "description": "Teh manis dingin khas warung.",
        "price": 3000,
        "image_url": "logo.jpeg",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Es Teh Manis",
        "description": "Teh dingin dengan gula sesuai selera.",
        "price": 5000,
        "image_url": "es teh manis.jfif",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Jus Mangga",
        "description": "Jus Mangga sehat, bisa request rasa.",
        "price": 10000,
        "image_url": "logo.jpeg",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Jus Alpukat",
        "description": "Jus alpukat creamy ala warung.",
        "price": 12000,
        "image_url": "logo.jpeg",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Jus Jambu",
        "description": "Jus jambu segar dengan rasa manis alami.",
        "price": 10000,
        "image_url": "jus jambu.jfif",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Jus Jeruk",
        "description": "Jus jeruk manis segar.",
        "price": 8000,
        "image_url": "logo.jpeg",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Kopi",
        "description": "Kopi hitam panas khas warung.",
        "price": 5000,
        "image_url": "logo.jpeg",
        "is_available": True,
    },
    {
        "category": "Minuman",
        "name": "Air Mineral",
        "description": "Air mineral dingin untuk pendamping menu utama.",
        "price": 4000,
        "image_url": "logo.jpeg",
        "is_available": True,
    },
]


def get_or_create_category(name: str, description: str | None = None) -> Category:
    """Ambil kategori dari DB, buat baru jika belum ada."""
    cat = Category.query.filter_by(name=name).first()
    if cat is None:
        cat = Category(name=name, description=description)
        db.session.add(cat)
        db.session.flush()  # dapat ID sebelum commit
        print(f"  [+] Kategori baru: {name}")
    else:
        print(f"  [=] Kategori sudah ada: {name}")
    return cat


def seed_categories() -> dict[str, Category]:
    """Seed semua kategori dan kembalikan map name → Category."""
    print("\n[1] Seeding Kategori...")
    cat_map: dict[str, Category] = {}
    for cat_data in CATEGORIES:
        cat = get_or_create_category(cat_data["name"], cat_data.get("description"))
        cat_map[cat_data["name"]] = cat
    return cat_map


def seed_menus(cat_map: dict[str, Category]) -> None:
    """Seed semua menu berdasarkan kategori."""
    print("\n[2] Seeding Menu...")
    created = 0
    skipped = 0

    for menu_data in MENUS:
        cat_name = menu_data["category"]
        cat = cat_map.get(cat_name)
        if cat is None:
            print(
                f"  [!] Kategori '{cat_name}' tidak ditemukan, skip: {menu_data['name']}"
            )
            skipped += 1
            continue

        # Skip jika nama menu sudah ada di tabel
        if Menu.query.filter_by(name=menu_data["name"]).first():
            print(f"  [=] Menu sudah ada: {menu_data['name']}")
            skipped += 1
            continue

        menu = Menu(
            category_id=cat.id,
            name=menu_data["name"],
            description=menu_data.get("description"),
            price=menu_data["price"],
            image_url=menu_data.get("image_url"),
            is_available=menu_data.get("is_available", True),
        )
        db.session.add(menu)
        print(f"  [+] Menu baru: {menu_data['name']} (Rp {menu_data['price']:,})")
        created += 1

    print(f"\n  Selesai: {created} menu ditambahkan, {skipped} dilewati.")


def main() -> None:
    print("=" * 55)
    print("  SEED MENU — Aplikasi Pemesanan Makanan")
    print("=" * 55)

    app = create_app()
    with app.app_context():
        cat_map = seed_categories()
        seed_menus(cat_map)
        db.session.commit()
        print("\n[OK] Data berhasil disimpan ke MySQL.\n")


if __name__ == "__main__":
    main()
