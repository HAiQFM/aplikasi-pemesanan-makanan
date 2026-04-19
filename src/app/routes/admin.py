"""
routes/admin.py — Panel administrasi: order management + menu CRUD.

Perubahan dari versi stub:
  - Menu CRUD (add/edit/delete) sekarang benar-benar menyimpan ke tabel `menus`
  - Kategori dapat dikelola dari tabel `categories`
  - Semua order management sudah otomatis via DB melalui order_store.py
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models import Category, Menu, db
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
    """Guard: hanya akun dengan role='admin' yang boleh akses /admin/*"""
    if session.get("user_role") != "admin":
        flash("Akses admin hanya untuk akun admin.", "error")
        return redirect(url_for("auth.login"))


# ── DASHBOARD ─────────────────────────────────────────────────────────────────


@admin_bp.route("/", methods=["GET"])
def dashboard():
    orders = list_orders()
    pending_payment_count = sum(
        1 for order in orders if order.get("status") == "Menunggu Pembayaran"
    )
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


# ── MENU CRUD ─────────────────────────────────────────────────────────────────


@admin_bp.route("/menus", methods=["GET"])
def menu_list():
    """READ — Daftar semua menu dari DB."""
    menus = Menu.query.join(Category).order_by(Category.name, Menu.name).all()
    return render_template("admin/menu_list.html", menus=menus)


@admin_bp.route("/menus/add", methods=["GET", "POST"])
def menu_add():
    """CREATE — Tambah menu baru ke tabel `menus`."""
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_id = request.form.get("category_id", "").strip()
        price = request.form.get("price", "0").strip()
        description = request.form.get("description", "").strip()
        image_url = request.form.get("image_url", "").strip()
        is_available = request.form.get("is_available") == "1"

        if not name or not category_id:
            flash("Nama menu dan kategori wajib diisi.", "error")
            return render_template("admin/menu_add.html", categories=categories)

        try:
            price_value = float(price) if price else 0.0
        except ValueError:
            flash("Format harga tidak valid.", "error")
            return render_template("admin/menu_add.html", categories=categories)

        # Cek duplikat nama
        if Menu.query.filter_by(name=name).first():
            flash(f"Menu dengan nama '{name}' sudah ada.", "error")
            return render_template("admin/menu_add.html", categories=categories)

        new_menu = Menu(
            name=name,
            category_id=int(category_id),
            price=price_value,
            description=description,
            image_url=image_url or None,
            is_available=is_available,
        )
        db.session.add(new_menu)
        db.session.commit()

        flash(f"Menu '{name}' berhasil ditambahkan.", "success")
        return redirect(url_for("admin.menu_list"))

    return render_template("admin/menu_add.html", categories=categories)


@admin_bp.route("/menus/<int:menu_id>/edit", methods=["GET", "POST"])
def menu_edit(menu_id: int):
    """UPDATE — Edit menu berdasarkan ID."""
    menu = Menu.query.get_or_404(menu_id)
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        menu.name = request.form.get("name", menu.name).strip()
        menu.category_id = int(request.form.get("category_id", menu.category_id))
        menu.description = request.form.get("description", "").strip()
        menu.image_url = request.form.get("image_url", "").strip() or None
        menu.is_available = request.form.get("is_available") == "1"

        price_raw = request.form.get("price", "").strip()
        try:
            menu.price = float(price_raw) if price_raw else menu.price
        except ValueError:
            flash("Format harga tidak valid.", "error")
            return render_template(
                "admin/menu_edit.html", menu=menu, categories=categories
            )

        db.session.commit()
        flash(f"Menu '{menu.name}' berhasil diperbarui.", "success")
        return redirect(url_for("admin.menu_list"))

    return render_template("admin/menu_edit.html", menu=menu, categories=categories)


@admin_bp.route("/menus/<int:menu_id>/delete", methods=["POST"])
def menu_delete(menu_id: int):
    """DELETE — Hapus menu dari DB (termasuk cart items terkait via cascade)."""
    menu = Menu.query.get_or_404(menu_id)
    name = menu.name
    db.session.delete(menu)
    db.session.commit()
    flash(f"Menu '{name}' berhasil dihapus.", "info")
    return redirect(url_for("admin.menu_list"))


# ── KATEGORI CRUD ─────────────────────────────────────────────────────────────


@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
    """CREATE + READ — Kelola kategori menu."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Nama kategori wajib diisi.", "error")
        elif Category.query.filter_by(name=name).first():
            flash(f"Kategori '{name}' sudah ada.", "error")
        else:
            db.session.add(Category(name=name, description=description or None))
            db.session.commit()
            flash(f"Kategori '{name}' berhasil ditambahkan.", "success")
        return redirect(url_for("admin.categories"))

    all_categories = Category.query.order_by(Category.name).all()
    return render_template("admin/category.html", categories=all_categories)


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
def category_delete(cat_id: int):
    """DELETE — Hapus kategori (akan gagal jika masih ada menu yang menggunakannya)."""
    cat = Category.query.get_or_404(cat_id)
    if cat.menus:
        flash(
            f"Kategori '{cat.name}' tidak dapat dihapus karena masih memiliki {len(cat.menus)} menu.",
            "error",
        )
        return redirect(url_for("admin.categories"))
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f"Kategori '{name}' berhasil dihapus.", "info")
    return redirect(url_for("admin.categories"))


# ── ORDER MANAGEMENT ──────────────────────────────────────────────────────────


@admin_bp.route("/orders", methods=["GET"])
def orders():
    """READ — Daftar semua pesanan dari DB."""
    all_orders = list_orders()
    return render_template("admin/orders.html", orders=all_orders)


@admin_bp.route("/orders/<int:order_id>/verify-payment", methods=["POST"])
def verify_payment(order_id: int):
    """UPDATE — Verifikasi pembayaran transfer/e-wallet."""
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
    """UPDATE — Ubah status pesanan."""
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
    """DELETE — Hapus pesanan dari DB (beserta order_items via cascade)."""
    deleted = delete_order(order_id)
    if not deleted:
        flash("Pesanan tidak ditemukan atau sudah dihapus.", "error")
        return redirect(url_for("admin.orders"))
    flash(f"Pesanan #{order_id} berhasil dihapus.", "info")
    return redirect(url_for("admin.orders"))
