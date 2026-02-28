from flask import Blueprint, flash, redirect, render_template, request, url_for

order_bp = Blueprint("order", __name__, url_prefix="/order")


@order_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        flash("Pesanan berhasil dibuat.", "success")
        return redirect(url_for("order.success"))
    return render_template("order/checkout.html")


@order_bp.route("/history", methods=["GET"])
def history():
    return render_template("order/history.html")


@order_bp.route("/success", methods=["GET"])
def success():
    return render_template("order/success.html")
