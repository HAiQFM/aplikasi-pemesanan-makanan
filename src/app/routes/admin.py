from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.order_store import (
    STATUS_LABELS,
    admin_sales_overview,
    daily_sales_report,
    delete_order,
    get_order,
    list_orders,
    update_order,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def require_admin():
    if session.get("user_role") != "admin":
        flash("Akses admin hanya untuk akun admin.", "error")
        return redirect(url_for("auth.login"))


@admin_bp.route("/", methods=["GET"])
def dashboard():
    orders = list_orders()
    pending_payment_count = sum(1 for order in orders if order.get("status") == "Menunggu Pembayaran")
    sales_report = daily_sales_report(limit=7)
    sales_overview = admin_sales_overview(transaction_limit=10, menu_limit=10)
    return render_template(
        "admin/dashboard.html",
        total_order=len(orders),
        pending_order=pending_payment_count,
        recent_orders=orders[:5],
        sales_report=sales_report,
        sales_overview=sales_overview,
    )


@admin_bp.route("/menus", methods=["GET"])
def menu_list():
    return render_template("admin/menu_list.html")


@admin_bp.route("/menus/add", methods=["GET", "POST"])
def menu_add():
    if request.method == "POST":
        flash("Menu baru berhasil ditambahkan.", "success")
        return redirect(url_for("admin.menu_list"))
    return render_template("admin/menu_add.html")


@admin_bp.route("/menus/<int:menu_id>/edit", methods=["GET", "POST"])
def menu_edit(menu_id: int):
    if request.method == "POST":
        flash(f"Menu #{menu_id} berhasil diperbarui.", "success")
        return redirect(url_for("admin.menu_list"))
    return render_template("admin/menu_edit.html", menu_id=menu_id)


@admin_bp.route("/menus/<int:menu_id>/delete", methods=["POST"])
def menu_delete(menu_id: int):
    flash(f"Menu #{menu_id} berhasil dihapus.", "info")
    return redirect(url_for("admin.menu_list"))


@admin_bp.route("/categories", methods=["GET"])
def categories():
    return render_template("admin/category.html")


@admin_bp.route("/orders", methods=["GET"])
def orders():
    all_orders = list_orders()
    return render_template("admin/orders.html", orders=all_orders)


@admin_bp.route("/orders/<int:order_id>/verify-payment", methods=["POST"])
def verify_payment(order_id: int):
    order = get_order(order_id)
    if not order:
        flash("Pesanan tidak ditemukan.", "error")
        return redirect(url_for("admin.orders"))

    if order.get("payment_method") not in {"transfer", "ewallet"}:
        flash("Verifikasi pembayaran hanya untuk transfer/e-wallet.", "error")
        return redirect(url_for("admin.orders"))

    if not order.get("payment_proof_path"):
        flash("Bukti pembayaran belum diunggah oleh pembeli.", "error")
        return redirect(url_for("admin.orders"))

    updated_status = order.get("status")
    if updated_status == "Menunggu Pembayaran":
        updated_status = "Sedang Dimasak"

    update_order(order_id, payment_verification="verified", status=updated_status)
    flash(f"Pembayaran pesanan #{order_id} berhasil diverifikasi.", "success")
    return redirect(url_for("admin.orders"))


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id: int):
    status = request.form.get("status", "").strip()
    if status not in STATUS_LABELS:
        flash("Status pesanan tidak valid.", "error")
        return redirect(url_for("admin.orders"))

    order = get_order(order_id)
    if not order:
        flash("Pesanan tidak ditemukan.", "error")
        return redirect(url_for("admin.orders"))

    update_order(order_id, status=status)
    flash(f"Status pesanan #{order_id} diperbarui menjadi {status}.", "success")
    return redirect(url_for("admin.orders"))


@admin_bp.route("/orders/<int:order_id>/delete", methods=["POST"])
def order_delete(order_id: int):
    deleted = delete_order(order_id)
    if not deleted:
        flash("Pesanan tidak ditemukan atau sudah dihapus.", "error")
        return redirect(url_for("admin.orders"))
    flash(f"Pesanan #{order_id} berhasil dihapus.", "info")
    return redirect(url_for("admin.orders"))
