from flask import Blueprint, flash, redirect, render_template, request, session, url_for

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
ADMIN_EMAIL = "ffaiqm14@gmail.com"
ADMIN_PASSWORD = "123456"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email == ADMIN_EMAIL:
            if password != ADMIN_PASSWORD:
                flash("Password admin salah.", "error")
                return render_template("auth/login.html")
            session["is_logged_in"] = True
            session["user_email"] = email
            session["user_name"] = "Admin"
            session["user_role"] = "admin"
            flash("Login admin berhasil.", "success")
            return redirect(url_for("admin.dashboard"))

        users = session.get("users", {})
        user_name = users.get(email)
        if not user_name:
            flash("Email tidak terdaftar, mohon registrasi terlebih dahulu.", "error")
            return render_template("auth/login.html")

        session["is_logged_in"] = True
        session["user_email"] = email
        session["user_name"] = user_name
        session["user_role"] = "customer"
        flash("Login berhasil.", "success")
        return redirect(url_for("order.history"))
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        if name and email:
            users = session.get("users", {})
            users[email] = name
            session["users"] = users

        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("is_logged_in", None)
    session.pop("user_email", None)
    session.pop("user_name", None)
    session.pop("user_role", None)
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout-admin", methods=["POST"])
def logout_admin():
    session.pop("is_logged_in", None)
    session.pop("user_email", None)
    session.pop("user_name", None)
    session.pop("user_role", None)
    flash("Admin logout berhasil.", "info")
    return redirect(url_for("main.index"))
