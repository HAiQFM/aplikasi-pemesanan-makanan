"""
scripts/migrate_json_to_db.py — Migrasi data lama ke MySQL.

Memigrasikan:
  1. Pengguna dari session (tidak bisa di-recover, akan dibuat ulang)
  2. Pesanan dari instance/orders.json → tabel orders + order_items

Jalankan SEKALI setelah database MySQL siap dan seed_menu.py sudah dijalankan:
    cd aplikasi-pemesanan-makanan
    python scripts/migrate_json_to_db.py

    Atau dengan path JSON kustom:
    python scripts/migrate_json_to_db.py --json-file path/ke/orders.json

CATATAN PENTING:
  - Script ini TIDAK menimpa data yang sudah ada di DB (cek berdasarkan ID).
  - Jalankan hanya sekali. Jika ada error, perbaiki lalu jalankan lagi —
    data yang sudah berhasil akan otomatis di-skip.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Tambahkan src/ ke Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import create_app
from app.models import Order, OrderItem, db

# Path default file JSON pesanan lama
DEFAULT_JSON_PATH = Path(__file__).parent.parent / "src" / "instance" / "orders.json"


def load_json_orders(json_path: Path) -> list[dict]:
    """Baca file JSON pesanan. Return list kosong jika file tidak ada."""
    if not json_path.exists():
        print(f"[!] File JSON tidak ditemukan: {json_path}")
        return []
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            print("[!] Format JSON tidak valid — ekspektasi array.")
            return []
        return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[!] Gagal membaca JSON: {exc}")
        return []


def parse_datetime(value: str) -> datetime:
    """Parse string ISO 8601 ke datetime, fallback ke sekarang."""
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return datetime.utcnow()


def migrate_order(order_data: dict) -> bool:
    """
    Migrasikan satu pesanan dari dict JSON ke tabel orders + order_items.
    Return True jika berhasil, False jika di-skip atau gagal.
    """
    order_id = order_data.get("id")
    if not order_id:
        print("  [!] Pesanan tanpa ID ditemukan, skip.")
        return False

    # Skip jika sudah ada di DB
    if db.session.get(Order, order_id):
        print(f"  [=] Pesanan #{order_id} sudah ada di DB, skip.")
        return False

    created_at = parse_datetime(order_data.get("created_at", ""))
    updated_at = parse_datetime(
        order_data.get("updated_at", "") or order_data.get("created_at", "")
    )

    # ── INSERT INTO orders ────────────────────────────────────────────────────
    order = Order(
        id=order_id,  # pertahankan ID lama
        user_id=None,  # tidak bisa di-recover dari JSON
        customer_name=str(order_data.get("customer_name", "") or "").strip(),
        customer_email=str(order_data.get("customer_email", "") or "").strip().lower(),
        address=str(order_data.get("address", "") or "").strip(),
        payment_method=str(order_data.get("payment_method", "") or ""),
        payment_proof_path=order_data.get("payment_proof_path"),
        payment_verification=str(
            order_data.get("payment_verification", "pending") or "pending"
        ),
        total_amount=int(order_data.get("total_amount", 0) or 0),
        status=str(
            order_data.get("status", "Menunggu Pembayaran") or "Menunggu Pembayaran"
        ),
        created_at=created_at,
        updated_at=updated_at,
    )
    db.session.add(order)
    db.session.flush()  # dapat order.id

    # ── INSERT INTO order_items ───────────────────────────────────────────────
    item_count = 0
    for item in order_data.get("items") or []:
        if not isinstance(item, dict):
            continue
        menu_name = str(item.get("name", "")).strip()
        if not menu_name:
            continue

        order_item = OrderItem(
            order_id=order.id,
            menu_name=menu_name,
            quantity=int(item.get("qty", 1) or 1),
            unit_price=int(item.get("price", 0) or 0),
            details=item.get("details") or [],
        )
        db.session.add(order_item)
        item_count += 1

    print(
        f"  [+] Pesanan #{order_id} | {order.customer_name} | "
        f"Rp {order.total_amount:,} | {order.status} | {item_count} item"
    )
    return True


def migrate_all(json_path: Path) -> None:
    """Migrasikan semua pesanan dari JSON ke DB."""
    print(f"\n[1] Membaca data dari: {json_path}")
    orders_data = load_json_orders(json_path)

    if not orders_data:
        print("  Tidak ada data untuk dimigrasi.")
        return

    print(f"  Ditemukan {len(orders_data)} pesanan.\n")
    print("[2] Memigrasikan pesanan ke MySQL...")

    success = 0
    skipped = 0
    failed = 0

    for order_data in orders_data:
        try:
            result = migrate_order(order_data)
            if result:
                success += 1
            else:
                skipped += 1
        except Exception as exc:
            order_id = order_data.get("id", "?")
            print(f"  [ERR] Pesanan #{order_id} gagal: {exc}")
            db.session.rollback()
            failed += 1

    db.session.commit()
    print(f"\n[RINGKASAN] Berhasil: {success} | Di-skip: {skipped} | Gagal: {failed}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrasikan pesanan dari orders.json ke MySQL"
    )
    parser.add_argument(
        "--json-file",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help=f"Path ke file orders.json (default: {DEFAULT_JSON_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Tampilkan data tanpa menyimpan ke DB",
    )
    args = parser.parse_args()

    print("=" * 55)
    print("  MIGRATE JSON → MySQL — Aplikasi Pemesanan Makanan")
    print("=" * 55)

    if args.dry_run:
        print("\n[MODE DRY-RUN] Data hanya ditampilkan, tidak disimpan.\n")
        orders_data = load_json_orders(args.json_file)
        for i, order in enumerate(orders_data, 1):
            print(
                f"  [{i}] #{order.get('id')} | {order.get('customer_name')} | "
                f"Rp {order.get('total_amount', 0):,} | {order.get('status')} | "
                f"{len(order.get('items', []))} item"
            )
        print(f"\nTotal: {len(orders_data)} pesanan.")
        return

    app = create_app()
    with app.app_context():
        migrate_all(args.json_file)
        print("\n[OK] Migrasi selesai.\n")


if __name__ == "__main__":
    main()
