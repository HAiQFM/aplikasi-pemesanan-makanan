"""
routes/admin.py - Panel administrasi untuk menu, kategori, stok bahan baku, dan pesanan.
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models import Category, Ingredient, Menu, db
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


def _safe_float(raw_value: str, fallback: float = 0.0) -> float:
    try:
        return float(str(raw_value).strip() or fallback)
    except (TypeError, ValueError):
        return fallback


def _low_stock_ingredients() -> list[Ingredient]:
    ingredients = Ingredient.query.filter_by(is_active=True).order_by(Ingredient.name).all()
    return [ingredient for ingredient in ingredients if ingredient.is_below_minimum]


@admin_bp.before_request
def require_admin():
    if session.get("user_role") != "admin":
        flash("Akses admin hanya untuk akun admin.", "error")
        return redirect(url_for("auth.login"))


@admin_bp.route("/", methods=["GET"])
def dashboard():
    orders = list_orders()
    pending_payment_count = sum(
        1 for order in orders if order.get("status") == "Menunggu Pembayaran"
    )
    sales_report = daily_sales_report(limit=7)
    sales_overview = admin_sales_overview(transaction_limit=10, menu_limit=10)
    low_stock_items = _low_stock_ingredients()
    active_ingredients = Ingredient.query.filter_by(is_active=True).count()

    return render_template(
        "admin/dashboard.html",
        total_menu=Menu.query.count(),
        total_category=Category.query.count(),
        total_order=len(orders),
        pending_order=pending_payment_count,
        recent_orders=orders[:5],
        sales_report=sales_report,
        sales_overview=sales_overview,
        total_ingredient=active_ingredients,
        low_stock_count=len(low_stock_items),
        low_stock_items=low_stock_items[:6],
    )


@admin_bp.route("/menus", methods=["GET"])
def menu_list():
    menus = Menu.query.join(Category).order_by(Category.name, Menu.name).all()
    return render_template("admin/menu_list.html", menus=menus)


@admin_bp.route("/menus/add", methods=["GET", "POST"])
def menu_add():
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
    menu = Menu.query.get_or_404(menu_id)
    name = menu.name
    db.session.delete(menu)
    db.session.commit()
    flash(f"Menu '{name}' berhasil dihapus.", "info")
    return redirect(url_for("admin.menu_list"))


@admin_bp.route("/categories", methods=["GET", "POST"])
def categories():
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


@admin_bp.route("/ingredients", methods=["GET", "POST"])
def ingredients():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        unit = request.form.get("unit", "").strip() or "pcs"
        current_stock = _safe_float(request.form.get("current_stock", "0"))
        minimum_stock = _safe_float(request.form.get("minimum_stock", "0"))
        note = request.form.get("note", "").strip()

        if not name:
            flash("Nama bahan baku wajib diisi.", "error")
            return redirect(url_for("admin.ingredients"))

        existing = Ingredient.query.filter(
            db.func.lower(Ingredient.name) == name.lower()
        ).first()
        if existing:
            flash(f"Bahan baku '{name}' sudah ada.", "error")
            return redirect(url_for("admin.ingredients"))

        ingredient = Ingredient(
            name=name,
            unit=unit,
            current_stock=current_stock,
            minimum_stock=minimum_stock,
            note=note or None,
        )
        db.session.add(ingredient)
        db.session.commit()
        flash(f"Bahan baku '{name}' berhasil ditambahkan.", "success")
        return redirect(url_for("admin.ingredients"))

    ingredients_list = Ingredient.query.order_by(Ingredient.name).all()
    low_stock_items = [item for item in ingredients_list if item.is_below_minimum]
    return render_template(
        "admin/ingredients.html",
        ingredients=ingredients_list,
        low_stock_items=low_stock_items,
    )


@admin_bp.route("/ingredients/<int:ingredient_id>/update", methods=["POST"])
def ingredient_update(ingredient_id: int):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    name = request.form.get("name", ingredient.name).strip()

    if not name:
        flash("Nama bahan baku wajib diisi.", "error")
        return redirect(url_for("admin.ingredients"))

    duplicate = Ingredient.query.filter(
        db.func.lower(Ingredient.name) == name.lower(),
        Ingredient.id != ingredient.id,
    ).first()
    if duplicate:
        flash(f"Nama bahan baku '{name}' sudah digunakan.", "error")
        return redirect(url_for("admin.ingredients"))

    ingredient.name = name
    ingredient.unit = request.form.get("unit", ingredient.unit).strip() or "pcs"
    ingredient.current_stock = _safe_float(
        request.form.get("current_stock", ingredient.current_stock),
        ingredient.stock_value,
    )
    ingredient.minimum_stock = _safe_float(
        request.form.get("minimum_stock", ingredient.minimum_stock),
        ingredient.minimum_value,
    )
    ingredient.note = request.form.get("note", ingredient.note or "").strip() or None
    ingredient.is_active = request.form.get("is_active") == "1"
    db.session.commit()

    if ingredient.is_below_minimum and ingredient.is_active:
        flash(
            f"Stok '{ingredient.name}' berada di bawah batas minimum. Segera lakukan restock.",
            "warning",
        )
    else:
        flash(f"Data bahan baku '{ingredient.name}' berhasil diperbarui.", "success")
    return redirect(url_for("admin.ingredients"))


@admin_bp.route("/ingredients/<int:ingredient_id>/delete", methods=["POST"])
def ingredient_delete(ingredient_id: int):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    name = ingredient.name
    db.session.delete(ingredient)
    db.session.commit()
    flash(f"Bahan baku '{name}' berhasil dihapus.", "info")
    return redirect(url_for("admin.ingredients"))


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

    if order.get("payment_method") not in {"transfer", "ewallet", "qris"}:
        flash("Verifikasi pembayaran hanya untuk transfer, e-wallet, atau QRIS.", "error")
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
