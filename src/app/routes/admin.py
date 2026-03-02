from flask import Blueprint, flash, redirect, render_template, request, url_for

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
def dashboard():
    return render_template("admin/dashboard.html")


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
    return render_template("admin/orders.html")
