from flask import Blueprint, flash, redirect, render_template, request, url_for

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.route("/", methods=["GET"])
def view_cart():
    return render_template("cart/cart.html")


@cart_bp.route("/add", methods=["POST"])
def add_to_cart():
    flash("Menu ditambahkan ke keranjang.", "success")
    return redirect(request.referrer or url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id: int):
    flash(f"Item #{item_id} dihapus dari keranjang.", "info")
    return redirect(url_for("cart.view_cart"))
