from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from app.models import Ingredient, db


@dataclass(frozen=True)
class BomIngredient:
    name: str
    unit: str
    quantity: Decimal


class InventoryUnitMismatch(ValueError):
    """Raised when BOM unit and ingredient master unit do not match."""


BASE_MODULES = {
    "nasi": [BomIngredient("Beras", "g", Decimal("200"))],
    "ayam": [BomIngredient("Ayam Potong", "pcs", Decimal("1"))],
}

CHICKEN_VARIATIONS = {
    "bakar": [
        BomIngredient("Bumbu Kuning", "g", Decimal("20")),
        BomIngredient("Kecap Manis", "ml", Decimal("15")),
    ],
    "geprek": [
        BomIngredient("Tepung Bumbu", "g", Decimal("50")),
        BomIngredient("Minyak Goreng", "ml", Decimal("30")),
    ],
    "penyet": [
        BomIngredient("Bumbu Kuning", "g", Decimal("20")),
        BomIngredient("Minyak Goreng", "ml", Decimal("30")),
    ],
}

SAMBAL_MODULES = {
    "ijo": [
        BomIngredient("Cabai Hijau", "g", Decimal("15")),
        BomIngredient("Tomat Hijau", "g", Decimal("10")),
        BomIngredient("Bawang Merah", "g", Decimal("5")),
    ],
    "hijau": [
        BomIngredient("Cabai Hijau", "g", Decimal("15")),
        BomIngredient("Tomat Hijau", "g", Decimal("10")),
        BomIngredient("Bawang Merah", "g", Decimal("5")),
    ],
    "merah": [
        BomIngredient("Cabai Merah/Rawit", "g", Decimal("20")),
        BomIngredient("Bawang Merah/Putih", "g", Decimal("8")),
        BomIngredient("Terasi", "g", Decimal("2")),
    ],
    "matah": [
        BomIngredient("Bawang Merah", "g", Decimal("15")),
        BomIngredient("Cabai Rawit", "g", Decimal("10")),
        BomIngredient("Serai & Daun Jeruk", "g", Decimal("5")),
        BomIngredient("Minyak Kelapa", "ml", Decimal("10")),
    ],
}

BEVERAGE_MODULES = {
    "fruit_juice": [
        BomIngredient("Buah Segar", "g", Decimal("150")),
        BomIngredient("Gula Pasir", "g", Decimal("20")),
        BomIngredient("SKM", "ml", Decimal("30")),
        BomIngredient("Es Batu", "g", Decimal("100")),
    ],
    "es_teh_manis": [
        BomIngredient("Teh Celup", "pcs", Decimal("1")),
        BomIngredient("Gula Pasir", "g", Decimal("20")),
        BomIngredient("Es Batu", "g", Decimal("100")),
    ],
    "air_mineral": [BomIngredient("Kemasan Air", "pcs", Decimal("1"))],
    "kopi": [BomIngredient("Kopi Saset", "pcs", Decimal("1"))],
}

FRUIT_JUICE_KEYWORDS = ("jus jambu", "jus mangga", "jus alpukat", "jus jeruk")
UNIT_ALIASES = {
    "gr": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "millilitre": "ml",
    "l": "liter",
    "lt": "liter",
    "liter": "liter",
    "litre": "liter",
    "pcs": "pcs",
    "pc": "pcs",
    "buah": "pcs",
    "sachet": "pcs",
}

UNIT_FACTORS = {
    ("g", "kg"): Decimal("0.001"),
    ("kg", "g"): Decimal("1000"),
    ("ml", "liter"): Decimal("0.001"),
    ("liter", "ml"): Decimal("1000"),
}


def _normalize(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _normalize_unit(unit: str) -> str:
    normalized = _normalize(unit)
    return UNIT_ALIASES.get(normalized, normalized)


def _convert_quantity(quantity: Decimal, from_unit: str, to_unit: str) -> Decimal:
    normalized_from = _normalize_unit(from_unit)
    normalized_to = _normalize_unit(to_unit)
    if normalized_from == normalized_to:
        return quantity

    factor = UNIT_FACTORS.get((normalized_from, normalized_to))
    if factor is None:
        raise InventoryUnitMismatch(
            f"Satuan bahan tidak kompatibel: BOM memakai {from_unit}, "
            f"tetapi master stok memakai {to_unit}."
        )
    return quantity * factor


def _selected_sambal(item: dict) -> str | None:
    for detail in item.get("details") or []:
        if not isinstance(detail, dict):
            continue
        if _normalize(detail.get("label", "")) == "sambal":
            return _normalize(detail.get("value", ""))

    item_name = _normalize(item.get("name", ""))
    if "sambal" not in item_name:
        return None
    return item_name


def _add_menu_unit_bom(item: dict) -> list[BomIngredient]:
    item_name = _normalize(item.get("name", ""))
    ingredients: list[BomIngredient] = []

    if "nasi" in item_name:
        ingredients.extend(BASE_MODULES["nasi"])

    if "ayam" in item_name:
        ingredients.extend(BASE_MODULES["ayam"])
        for keyword, module in CHICKEN_VARIATIONS.items():
            if keyword in item_name:
                ingredients.extend(module)
                break

    selected_sambal = _selected_sambal(item)
    if selected_sambal:
        for keyword, module in SAMBAL_MODULES.items():
            if keyword in selected_sambal:
                ingredients.extend(module)
                break

    if any(keyword in item_name for keyword in FRUIT_JUICE_KEYWORDS):
        ingredients.extend(BEVERAGE_MODULES["fruit_juice"])
    elif "es teh manis" in item_name:
        ingredients.extend(BEVERAGE_MODULES["es_teh_manis"])
    elif "air mineral" in item_name:
        ingredients.extend(BEVERAGE_MODULES["air_mineral"])
    elif "kopi" in item_name:
        ingredients.extend(BEVERAGE_MODULES["kopi"])

    return ingredients


def build_deduction_list(items: list[dict] | None) -> list[dict]:
    totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)

    for item in items or []:
        if not isinstance(item, dict):
            continue
        quantity = Decimal(str(int(item.get("qty", 0) or 0)))
        if quantity <= 0:
            continue

        for ingredient in _add_menu_unit_bom(item):
            key = (ingredient.name, ingredient.unit)
            totals[key] += ingredient.quantity * quantity

    return [
        {
            "ingredient_name": name,
            "unit": unit,
            "quantity_deducted": float(quantity),
        }
        for (name, unit), quantity in sorted(totals.items(), key=lambda row: row[0][0])
    ]


def deduct_inventory_for_items(items: list[dict] | None) -> list[dict]:
    deduction_rows = build_deduction_list(items)
    if not deduction_rows:
        return []

    results = []
    for row in deduction_rows:
        ingredient_name = row["ingredient_name"]
        unit = row["unit"]
        deducted = Decimal(str(row["quantity_deducted"]))

        ingredient = Ingredient.query.filter(
            db.func.lower(Ingredient.name) == ingredient_name.lower()
        ).first()
        if ingredient is None:
            ingredient = Ingredient(
                name=ingredient_name,
                unit=unit,
                current_stock=Decimal("0"),
                minimum_stock=Decimal("0"),
                note="Dibuat otomatis oleh sistem deduksi transaksi.",
            )
            db.session.add(ingredient)
            db.session.flush()
        deducted = _convert_quantity(deducted, unit, ingredient.unit)

        remaining = Decimal(ingredient.current_stock or 0) - deducted
        ingredient.current_stock = remaining
        results.append(
            {
                "ingredient_name": ingredient.name,
                "unit": ingredient.unit,
                "quantity_deducted": float(deducted),
                "remaining_stock": float(remaining),
            }
        )

    return results
