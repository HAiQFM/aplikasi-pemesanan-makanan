import json
from datetime import date, datetime
from pathlib import Path

from flask import current_app

STATUS_LABELS = [
    "Menunggu Pembayaran",
    "Sedang Dimasak",
    "Dalam Perjalanan",
    "Selesai",
    "Dibatalkan",
]


def _store_path() -> Path:
    configured_path = current_app.config.get("ORDER_STORE_FILE")
    if configured_path:
        path = Path(configured_path)
    else:
        path = Path(current_app.instance_path) / "orders.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_raw_orders() -> list[dict]:
    path = _store_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _save_raw_orders(orders: list[dict]) -> None:
    path = _store_path()
    path.write_text(json.dumps(orders, ensure_ascii=True, indent=2), encoding="utf-8")


def list_orders(customer_email: str | None = None) -> list[dict]:
    orders = _load_raw_orders()
    if customer_email:
        customer_email = customer_email.strip().lower()
        orders = [item for item in orders if item.get("customer_email") == customer_email]
    return sorted(orders, key=lambda item: item.get("created_at", ""), reverse=True)


def get_order(order_id: int) -> dict | None:
    for order in _load_raw_orders():
        if order.get("id") == order_id:
            return order
    return None


def create_order(
    customer_name: str,
    customer_email: str,
    address: str,
    payment_method: str,
    total_amount: int,
    items: list[dict] | None = None,
    payment_proof_path: str | None = None,
) -> dict:
    orders = _load_raw_orders()
    next_id = max((item.get("id", 0) for item in orders), default=0) + 1

    status = "Sedang Dimasak" if payment_method == "cash" else "Menunggu Pembayaran"
    payment_verification = "verified" if payment_method == "cash" else "pending"

    order = {
        "id": next_id,
        "customer_name": customer_name,
        "customer_email": customer_email.strip().lower(),
        "address": address,
        "payment_method": payment_method,
        "payment_proof_path": payment_proof_path,
        "payment_verification": payment_verification,
        "total_amount": int(total_amount),
        "items": items or [],
        "status": status,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    orders.append(order)
    _save_raw_orders(orders)
    return order


def update_order(order_id: int, **updates) -> dict | None:
    orders = _load_raw_orders()
    updated = None
    for item in orders:
        if item.get("id") != order_id:
            continue
        item.update(updates)
        item["updated_at"] = datetime.now().isoformat(timespec="seconds")
        updated = item
        break
    if updated is not None:
        _save_raw_orders(orders)
    return updated


def delete_order(order_id: int) -> bool:
    orders = _load_raw_orders()
    original_count = len(orders)
    orders = [item for item in orders if item.get("id") != order_id]
    if len(orders) == original_count:
        return False
    _save_raw_orders(orders)
    return True


def status_counts(customer_email: str | None = None) -> dict[str, int]:
    counts = {label: 0 for label in STATUS_LABELS}
    for order in list_orders(customer_email=customer_email):
        status = order.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def daily_sales_report(limit: int = 7) -> dict:
    report_by_day: dict[str, dict] = {}

    for order in list_orders():
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

    rows = sorted(report_by_day.values(), key=lambda item: item["date"], reverse=True)
    for row in rows:
        valid_order_count = row["order_count"] - row["canceled_count"]
        row["average_sales"] = int(row["gross_sales"] / valid_order_count) if valid_order_count > 0 else 0

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

    return {
        "today": today,
        "rows": rows[:limit],
    }


def admin_sales_overview(transaction_limit: int = 10, menu_limit: int = 10) -> dict:
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
                ) or "-",
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
                menu_name,
                {
                    "name": menu_name,
                    "qty_sold": 0,
                    "revenue": 0,
                },
            )
            menu_report["qty_sold"] += quantity
            menu_report["revenue"] += quantity * price

    menu_rows = sorted(
        menu_totals.values(),
        key=lambda item: (item["qty_sold"], item["revenue"], item["name"].lower()),
        reverse=True,
    )

    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "menu_rows": menu_rows[:menu_limit],
        "transactions": transactions[:transaction_limit],
    }
