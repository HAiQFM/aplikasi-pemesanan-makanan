from flask import Blueprint, flash, redirect, render_template, request, url_for

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Login berhasil.", "success")
        return redirect(url_for("order.history"))
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))
