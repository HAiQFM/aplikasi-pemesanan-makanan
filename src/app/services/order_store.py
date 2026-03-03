import json
from datetime import datetime
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
