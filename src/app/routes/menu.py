from flask import Blueprint, render_template

menu_bp = Blueprint("menu", __name__, url_prefix="/menu")



@menu_bp.route("/")
def index():
    menu_items = [
        {
            "name": "Nasi Ayam Geprek",
            "category": "Paket Ayam",
            "price": "Rp 13.000",
            "price_value": 13000,
            "desc": "Ayam geprek crispy dengan nasi hangat.",
            "image": "Nasi-Ayam-Geprek.jpg",
        },
        {
            "name": "Nasi Ayam Bakar",
            "category": "Paket Ayam",
            "price": "Rp 13.000",
            "price_value": 13000,
            "desc": "Ayam bakar bumbu manis gurih dengan nasi.",
            "image": "Nasi-ayam-bakar.jpg",
        },
        {
            "name": "Nasi Ayam Penyet",
            "category": "Paket Ayam",
            "price": "Rp 13.000",
            "price_value": 13000,
            "desc": "Ayam penyet empuk dengan lalapan segar.",
            "image": "Nasi-Ayam-penyet.png",
        },
    ]
    drink_items = [
        {"name": "Tea Jus", "category": "Minuman", "price": "Rp 3.000", "price_value": 3000, "desc": "Teh manis dingin khas warung.", "image": "Tea-jus.jpg"},
        {"name": "Es Teh Manis", "category": "Minuman", "price": "Rp 5.000", "price_value": 5000, "desc": "Teh dingin dengan gula sesuai selera.", "image": "Es-Teh-Manis.jpg"},
        {"name": "Jus Mangga", "category": "Minuman", "price": "Rp 10.000", "price_value": 10000, "desc": "Jus Mangga sehat, bisa request rasa.", "image": "Jus-mangga.jpeg"},
        {"name": "Jus Alpukat", "category": "Minuman", "price": "Rp 12.000", "price_value": 12000, "desc": "Jus alpukat creamy ala warung.", "image": "Jus-Alpukat.jpg"},
        {"name": "Jus Jambu", "category": "Minuman", "price": "Rp 10.000", "price_value": 10000, "desc": "Jus jambu segar dengan rasa manis alami.", "image": "Jus-Jambu.jpg"},
        {"name": "Jus Jeruk", "category": "Minuman", "price": "Rp 8.000", "price_value": 8000, "desc": "Jus jeruk manis segar.", "image": "Jus-Jeruk.jpg"},
        {"name": "Kopi", "category": "Minuman", "price": "Rp 5.000", "price_value": 5000, "desc": "Kopi hitam panas khas warung.", "image": "kopi.jpg"},
        {"name": "Air Mineral", "category": "Minuman", "price": "Rp 4.000", "price_value": 4000, "desc": "Air mineral dingin untuk pendamping menu utama.", "image": "air-mineral.jpg"},
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

