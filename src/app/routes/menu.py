from flask import Blueprint, render_template

menu_bp = Blueprint("menu", __name__, url_prefix="/menu")



@menu_bp.route("/")
def index():
    menu_items = [
        {
            "name": "Nasi Ayam Geprek",
            "category": "Paket Ayam",
            "price": "Rp 13.000",
            "desc": "Ayam geprek crispy dengan nasi hangat.",
        },
        {
            "name": "Nasi Ayam Bakar",
            "category": "Paket Ayam",
            "price": "Rp 13.000",
            "desc": "Ayam bakar bumbu manis gurih dengan nasi.",
        },
        {
            "name": "Nasi Ayam Penyet",
            "category": "Paket Ayam",
            "price": "Rp 13.000",
            "desc": "Ayam penyet empuk dengan lalapan segar.",
        },
    ]
    drink_items = [
        {"name": "Tea Jus", "category": "Minuman", "price": "Rp 3.000", "desc": "Teh manis dingin khas warung."},
        {"name": "Es Teh Manis", "category": "Minuman", "price": "Rp 5.000", "desc": "Teh hangat dengan gula sesuai selera."},
        {"name": "Jus Jeruk", "category": "Minuman", "price": "Rp 10.000", "desc": "Jus jeruk segar, bisa request rasa."},
        {"name": "Jus Alpukat", "category": "Minuman", "price": "Rp 12.000", "desc": "Jus alpukat creamy ala warung."},
        {"name": "Es Jeruk", "category": "Minuman", "price": "Rp 8.000", "desc": "Es jeruk manis segar."},
        {"name": "Kopi", "category": "Minuman", "price": "Rp 5.000", "desc": "Kopi hitam panas khas warung."},
    ]
    sambal_options = ["Sambal Merah", "Sambal Ijo", "Sambal Matah"]
    return render_template(
        "menu/index.html",
        menu_items=menu_items,
        drink_items=drink_items,
        sambal_options=sambal_options,
    )

@menu_bp.route("/", methods=["GET"])
def catalog():
    return render_template("menu/catalog.html")


@menu_bp.route("/<int:menu_id>", methods=["GET"])
def detail(menu_id: int):
    return render_template("menu/detail.html", menu_id=menu_id)

