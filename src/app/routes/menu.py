from flask import Blueprint, render_template

menu_bp = Blueprint("menu", __name__, url_prefix="/menu")


@menu_bp.route("/", methods=["GET"])
def catalog():
    return render_template("menu/catalog.html")


@menu_bp.route("/<int:menu_id>", methods=["GET"])
def detail(menu_id: int):
    return render_template("menu/detail.html", menu_id=menu_id)
