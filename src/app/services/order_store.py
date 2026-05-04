"""
order_store.py — Service layer untuk operasi CRUD pesanan via MySQL.

Semua fungsi mempertahankan signature dan format return yang sama dengan
versi JSON sebelumnya sehingga routes tidak perlu diubah secara besar-besaran.

Alur data:
    routes/order.py  ──►  order_store.py  ──►  SQLAlchemy (MySQL)
    routes/admin.py  ──►  order_store.py  ──►  SQLAlchemy (MySQL)
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func

from app.models import Cart, Order, OrderItem, db
from app.services.inventory import deduct_inventory_for_items

# Label status yang valid — urut sesuai alur pesanan
STATUS_LABELS = [
    "Menunggu Pembayaran",
    "Sedang Dimasak",
    "Dalam Perjalanan",
    "Selesai",
    "Dibatalkan",
]


# ── READ ──────────────────────────────────────────────────────────────────────


def list_orders(customer_email: str | None = None) -> list[dict]:
    """
    Baca semua pesanan dari DB, opsional filter berdasarkan customer_email.
    Mengembalikan list dict yang kompatibel dengan template Jinja2.

    Pengganti: JSON filter di _load_raw_orders()
    """
    query = Order.query.order_by(Order.created_at.desc())
    if customer_email:
        query = query.filter(Order.customer_email == customer_email.strip().lower())
    return [order.to_dict() for order in query.all()]


def get_order(order_id: int) -> dict | None:
    """
    Ambil satu pesanan berdasarkan ID.
    Return None jika tidak ditemukan.

    Pengganti: loop pencarian di _load_raw_orders()
    """
    order = db.session.get(Order, order_id)
    return order.to_dict() if order else None


# ── CREATE ────────────────────────────────────────────────────────────────────


def create_order(
    customer_name: str,
    customer_email: str,
    address: str,
    payment_method: str,
    total_amount: int,
    items: list[dict] | None = None,
    payment_proof_path: str | None = None,
    user_id: int | None = None,  # ← baru: FK ke users.id (None untuk tamu)
) -> dict:
    """
    Simpan pesanan baru ke MySQL dalam satu transaksi atomik.

    Parameter items format:
        [{"name": str, "qty": int, "price": int, "details": list}]

    Pengganti: append ke JSON + _save_raw_orders()
    """
    try:
        # Tentukan status awal berdasarkan metode pembayaran
        if payment_method == "cash":
            initial_status = "Sedang Dimasak"
            payment_verification = "verified"
        else:
            initial_status = "Menunggu Pembayaran"
            payment_verification = "pending"

        order = Order(
            user_id=user_id,
            customer_name=customer_name.strip(),
            customer_email=customer_email.strip().lower(),
            address=address.strip(),
            payment_method=payment_method,
            payment_proof_path=payment_proof_path,
            payment_verification=payment_verification,
            total_amount=int(total_amount),
            status=initial_status,
        )
        db.session.add(order)
        db.session.flush()  # dapatkan order.id sebelum commit

        # Simpan setiap item pesanan ke tabel order_items
        for item in items or []:
            if not isinstance(item, dict):
                continue
            order_item = OrderItem(
                order_id=order.id,
                menu_name=str(item.get("name", "")).strip(),
                quantity=int(item.get("qty", 1) or 1),
                unit_price=int(item.get("price", 0) or 0),
                details=item.get("details") or [],  # JSON: [{"label": ..., "value": ...}]
            )
            db.session.add(order_item)

        inventory_deductions = deduct_inventory_for_items(items)
        order.inventory_deductions = inventory_deductions
        if user_id is not None:
            Cart.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.commit()

        order_data = order.to_dict()
        return order_data
    except Exception:
        db.session.rollback()
        raise


# ── UPDATE ────────────────────────────────────────────────────────────────────


def update_order(order_id: int, **updates) -> dict | None:
    """
    Update field pesanan secara dinamis menggunakan keyword arguments.
    Contoh: update_order(1, status="Selesai", payment_verification="verified")

    Pengganti: item.update(updates) + _save_raw_orders()
    """
    order = db.session.get(Order, order_id)
    if order is None:
        return None

    # Daftar kolom yang boleh diupdate dari luar
    ALLOWED_FIELDS = {
        "status",
        "payment_method",
        "payment_proof_path",
        "payment_verification",
        "total_amount",
        "customer_name",
        "customer_email",
        "address",
    }

    for key, value in updates.items():
        if key in ALLOWED_FIELDS and hasattr(order, key):
            setattr(order, key, value)

    order.updated_at = datetime.utcnow()
    db.session.commit()
    return order.to_dict()


# ── DELETE ────────────────────────────────────────────────────────────────────


def delete_order(order_id: int) -> bool:
    """
    Hapus pesanan dan semua order_items terkait (CASCADE via relasi SQLAlchemy).
    Return True jika berhasil, False jika pesanan tidak ditemukan.

    Pengganti: filter JSON + _save_raw_orders()
    """
    order = db.session.get(Order, order_id)
    if order is None:
        return False
    db.session.delete(order)  # cascade akan hapus order_items otomatis
    db.session.commit()
    return True


# ── ANALITIK & LAPORAN ────────────────────────────────────────────────────────


def status_counts(customer_email: str | None = None) -> dict[str, int]:
    """Hitung jumlah pesanan per status."""
    counts = {label: 0 for label in STATUS_LABELS}
    query = db.session.query(Order.status, func.count(Order.id))
    if customer_email:
        query = query.filter(Order.customer_email == customer_email.strip().lower())
    for status, count in query.group_by(Order.status).all():
        if status in counts:
            counts[status] = count
    return counts


def daily_sales_report(limit: int = 7) -> dict:
    """
    Laporan penjualan harian (limit hari terakhir).
    Mengembalikan dict dengan key "today" dan "rows" (list laporan per hari).
    """
    # Ambil semua order dari DB sebagai dict (agregasi dilakukan di Python
    # untuk mempertahankan kompatibilitas logika lama)
    orders = [o.to_dict() for o in Order.query.order_by(Order.created_at.asc()).all()]

    report_by_day: dict[str, dict] = {}

    for order in orders:
        created_at = str(order.get("created_at", "")).strip()
        total_amount = int(order.get("total_amount", 0) or 0)
        status = str(order.get("status", "")).strip()

        try:
            order_date = datetime.fromisoformat(created_at).date()
        except ValueError:
            continue

        day_key = order_date.isoformat()
        day_report = report_by_day.setdefault(
            day_key,
            {
                "date": day_key,
                "label": order_date.strftime("%d %b %Y"),
                "order_count": 0,
                "completed_count": 0,
                "canceled_count": 0,
                "gross_sales": 0,
            },
        )

        day_report["order_count"] += 1
        if status == "Selesai":
            day_report["completed_count"] += 1
        if status == "Dibatalkan":
            day_report["canceled_count"] += 1
            continue
        day_report["gross_sales"] += total_amount

    rows = sorted(report_by_day.values(), key=lambda r: r["date"], reverse=True)
    for row in rows:
        valid_count = row["order_count"] - row["canceled_count"]
        row["average_sales"] = (
            int(row["gross_sales"] / valid_count) if valid_count > 0 else 0
        )

    today_key = date.today().isoformat()
    today = next(
        (row for row in rows if row["date"] == today_key),
        {
            "date": today_key,
            "label": date.today().strftime("%d %b %Y"),
            "order_count": 0,
            "completed_count": 0,
            "canceled_count": 0,
            "gross_sales": 0,
            "average_sales": 0,
        },
    )

    return {"today": today, "rows": rows[:limit]}


def admin_sales_overview(transaction_limit: int = 10, menu_limit: int = 10) -> dict:
    """
    Overview penjualan untuk dashboard admin:
    - Total revenue & transaksi
    - Menu terlaris
    - Daftar transaksi terbaru
    """
    menu_totals: dict[str, dict] = {}
    transactions: list[dict] = []
    total_revenue = 0
    total_transactions = 0

    for order in list_orders():
        status = str(order.get("status", "")).strip()
        total_amount = int(order.get("total_amount", 0) or 0)
        is_canceled = status == "Dibatalkan"

        transactions.append(
            {
                "id": order.get("id"),
                "customer_name": order.get("customer_name") or "Pelanggan",
                "status": status or "-",
                "total_amount": total_amount,
                "created_at": str(order.get("created_at", "")).replace("T", " "),
                "item_summary": ", ".join(
                    f"{int(item.get('qty', 0) or 0)}x {str(item.get('name', '')).strip()}".strip()
                    for item in order.get("items", [])
                    if isinstance(item, dict) and str(item.get("name", "")).strip()
                )
                or "-",
            }
        )

        if is_canceled:
            continue

        total_transactions += 1
        total_revenue += total_amount

        for item in order.get("items", []):
            if not isinstance(item, dict):
                continue
            menu_name = str(item.get("name", "")).strip()
            quantity = int(item.get("qty", 0) or 0)
            price = int(item.get("price", 0) or 0)
            if not menu_name or quantity <= 0:
                continue

            menu_report = menu_totals.setdefault(
                menu_name, {"name": menu_name, "qty_sold": 0, "revenue": 0}
            )
            menu_report["qty_sold"] += quantity
            menu_report["revenue"] += quantity * price

    menu_rows = sorted(
        menu_totals.values(),
        key=lambda r: (r["qty_sold"], r["revenue"], r["name"].lower()),
        reverse=True,
    )

    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "menu_rows": menu_rows[:menu_limit],
        "transactions": transactions[:transaction_limit],
    }
