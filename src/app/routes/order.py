"""
routes/order.py — Endpoint checkout, riwayat, dan upload bukti bayar.

Perubahan dari versi JSON:
  - create_order() sekarang menerima user_id (FK ke users) untuk user yang login
  - Tamu (guest) tetap bisa checkout tanpa akun — user_id=None di DB
"""

import os
import json
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app.services.order_store import create_order, get_order, list_orders, update_order

order_bp = Blueprint("order", __name__, url_prefix="/order")
ALLOWED_PROOF_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
TRANSFER_ACCOUNT = "BANK BRI 4371 0103 3691 530"
EWALLET_ACCOUNT = "DANA +62 813 1291 0980"


def _parse_total_amount(raw_value: str) -> int:
    numeric = "".join(ch for ch in (raw_value or "") if ch.isdigit())
    return int(numeric) if numeric else 0


def _current_customer_key() -> str:
    """
    Kembalikan identifier pelanggan: email jika login, atau guest key.
    Digunakan sebagai customer_email di tabel orders.
    """
    user_email = session.get("user_email", "").strip().lower()
    if user_email:
        return user_email
    guest_key = session.get("guest_customer_key")
    if not guest_key:
        guest_key = f"guest-{os.urandom(8).hex()}@local"
        session["guest_customer_key"] = guest_key
    return guest_key


def _current_user_id() -> int | None:
    """
    Kembalikan user_id dari session (untuk FK ke tabel users).
    Return None untuk tamu yang tidak login.
    """
    if session.get("is_logged_in"):
        return session.get("user_id")
    return None


def _parse_checkout_items(raw_value: str) -> list[dict]:
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []

    normalized = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        qty = int(item.get("qty", 0) or 0)
        price = int(item.get("price", 0) or 0)
        if not name or qty <= 0 or price < 0:
            continue
        raw_details = item.get("details", [])
        details = []
        if isinstance(raw_details, list):
            for detail in raw_details:
                if not isinstance(detail, dict):
                    continue
                label = str(detail.get("label", "")).strip()
                value = str(detail.get("value", "")).strip()
                if label and value:
                    details.append({"label": label, "value": value})
        normalized.append(
            {"name": name, "qty": qty, "price": price, "details": details}
        )
    return normalized


def _is_allowed_proof_file(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_PROOF_EXTENSIONS


def _save_payment_proof(order_id: int, uploaded_file) -> str:
    uploads_dir = Path(current_app.static_folder) / "uploads" / "payment-proofs"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(uploaded_file.filename or "")
    extension = filename.rsplit(".", 1)[1].lower()
    stored_name = f"order_{order_id}_{session.get('user_email', 'guest').replace('@', '_at_')}.{extension}"
    destination = uploads_dir / stored_name
    uploaded_file.save(destination)
    return os.path.join("uploads", "payment-proofs", stored_name).replace("\\", "/")


# ── CHECKOUT (CREATE) ─────────────────────────────────────────────────────────


@order_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    """
    CREATE — Simpan pesanan baru ke tabel `orders` + `order_items`.

    Sebelumnya: append ke orders.json
    Sekarang  : INSERT INTO orders (...) + INSERT INTO order_items (...)
    """
    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        address = request.form.get("address", "").strip()
        payment_method = request.form.get("payment_method", "").strip().lower()
        total_amount = _parse_total_amount(request.form.get("order_total", "0"))
        order_items = _parse_checkout_items(request.form.get("checkout_items", ""))

        if payment_method not in {"cash", "transfer", "ewallet"}:
            flash("Metode pembayaran tidak valid.", "error")
            return redirect(url_for("order.checkout"))

        payment_proof = request.files.get("payment_proof")
        requires_proof = payment_method in {"transfer", "ewallet"}
        if requires_proof:
            if not payment_proof or not payment_proof.filename:
                flash(
                    "Bukti pembayaran wajib diunggah untuk transfer bank atau e-wallet.",
                    "error",
                )
                return redirect(url_for("order.checkout"))
            if not _is_allowed_proof_file(payment_proof.filename):
                flash(
                    "Format bukti pembayaran harus PNG, JPG, JPEG, atau PDF.", "error"
                )
                return redirect(url_for("order.checkout"))

        # CREATE — kirim user_id agar pesanan terhubung ke akun (None untuk tamu)
        order = create_order(
            customer_name=customer_name,
            customer_email=_current_customer_key(),
            address=address,
            payment_method=payment_method,
            total_amount=total_amount,
            items=order_items,
            payment_proof_path=None,
            user_id=_current_user_id(),  # ← FK ke users.id
        )

        if requires_proof and payment_proof:
            proof_path = _save_payment_proof(order["id"], payment_proof)
            # UPDATE — simpan path bukti bayar ke DB
            update_order(
                order["id"],
                payment_proof_path=proof_path,
                payment_verification="pending",
            )

        if payment_method == "cash":
            flash(
                "Pesanan COD berhasil dibuat dan masuk ke status Sedang Dimasak.",
                "success",
            )
        elif payment_method == "transfer":
            flash(
                f"Pembayaran transfer diterima. Rekening tujuan: {TRANSFER_ACCOUNT}. Menunggu verifikasi admin.",
                "info",
            )
        else:
            flash(
                f"Pembayaran e-wallet diterima. Nomor tujuan: {EWALLET_ACCOUNT}. Menunggu verifikasi admin.",
                "info",
            )

        session["latest_order_id"] = order["id"]
        return redirect(url_for("order.success"))

    customer_name = ""
    if session.get("is_logged_in"):
        customer_name = session.get("user_name", "")
    return render_template(
        "order/checkout.html",
        customer_name=customer_name,
        transfer_account=TRANSFER_ACCOUNT,
        ewallet_account=EWALLET_ACCOUNT,
    )


# ── RIWAYAT PESANAN (READ) ────────────────────────────────────────────────────


@order_bp.route("/history", methods=["GET"])
def history():
    """
    READ — Ambil riwayat pesanan dari DB berdasarkan customer_email.

    Sebelumnya: filter list dari orders.json
    Sekarang  : SELECT * FROM orders WHERE customer_email = ? ORDER BY created_at DESC
    """
    orders = list_orders(customer_email=_current_customer_key())
    return render_template("order/history.html", orders=orders)


# ── UPLOAD BUKTI BAYAR (UPDATE) ───────────────────────────────────────────────


@order_bp.route("/<int:order_id>/upload-proof", methods=["POST"])
def upload_payment_proof(order_id: int):
    """
    UPDATE — Perbarui payment_proof_path di tabel `orders`.

    Sebelumnya: update dict di orders.json
    Sekarang  : UPDATE orders SET payment_proof_path = ?, updated_at = NOW() WHERE id = ?
    """
    if not session.get("is_logged_in"):
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("auth.login"))

    order = get_order(order_id)
    user_email = session.get("user_email", "").strip().lower()
    if not order or order.get("customer_email") != user_email:
        flash("Pesanan tidak ditemukan.", "error")
        return redirect(url_for("order.history"))

    payment_method = order.get("payment_method")
    if payment_method not in {"transfer", "ewallet"}:
        flash("Bukti pembayaran hanya untuk transfer atau e-wallet.", "error")
        return redirect(url_for("order.history"))

    payment_proof = request.files.get("payment_proof")
    if not payment_proof or not payment_proof.filename:
        flash("Pilih file bukti pembayaran terlebih dahulu.", "error")
        return redirect(url_for("order.history"))

    if not _is_allowed_proof_file(payment_proof.filename):
        flash("Format bukti pembayaran harus PNG, JPG, JPEG, atau PDF.", "error")
        return redirect(url_for("order.history"))

    proof_path = _save_payment_proof(order_id, payment_proof)
    update_order(
        order_id, payment_proof_path=proof_path, payment_verification="pending"
    )
    flash("Bukti pembayaran berhasil diunggah. Menunggu verifikasi admin.", "success")
    return redirect(url_for("order.history"))


# ── HALAMAN SUKSES ────────────────────────────────────────────────────────────


@order_bp.route("/success", methods=["GET"])
def success():
    order = None
    raw_order_id = request.args.get("order_id", "").strip()
    if raw_order_id.isdigit():
        order = get_order(int(raw_order_id))
    elif str(session.get("latest_order_id", "")).isdigit():
        order = get_order(int(session.get("latest_order_id")))
    return render_template("order/success.html", order=order)
