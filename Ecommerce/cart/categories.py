"""
Map raw CSV / marketplace categories into a fixed set of OptiCart categories.
"""

import re

STANDARD_CATEGORIES = [
    "Electronics",
    "Fashion",
    "Home & Furniture",
    "Beauty & Personal Care",
    "Sports & Fitness",
    "Books & Media",
    "Toys & Kids",
    "Grocery & Food",
    "Automotive",
    "Others",
]

# (standard name, keywords matched in category path + product name)
_CATEGORY_RULES = [
    (
        "Electronics",
        [
            "electronic", "electronics", "phone", "mobile", "smartphone",
            "laptop", "computer", "tablet", "tv", "television", "camera",
            "audio", "headphone", "earphone", "speaker", "monitor",
            "processor", "gaming", "console", "wearable", "smartwatch",
            "appliance", "refrigerator", "washing", "microwave", "ac ",
            "air conditioner", "toner", "printer",
        ],
    ),
    (
        "Fashion",
        [
            "clothing", "fashion", "apparel", "women", "men", "kids wear",
            "footwear", "shoe", "sandal", "watch", "jewellery", "jewelry",
            "bag", "handbag", "wallet", "lingerie", "top", "shirt", "dress",
            "jeans", "shorts", "kurta", "saree", "ethnic",
        ],
    ),
    (
        "Home & Furniture",
        [
            "furniture", "home", "kitchen", "dining", "decor", "bedroom",
            "living room", "sofa", "mattress", "curtain", "lighting",
            "storage", "garden", "tool", "hardware", "showpiece",
            "display unit", "dinner set", "cookware",
        ],
    ),
    (
        "Beauty & Personal Care",
        [
            "beauty", "personal care", "cosmetic", "skin", "hair",
            "fragrance", "perfume", "makeup", "grooming", "health",
            "wellness", "supplement", "vitamin",
        ],
    ),
    (
        "Sports & Fitness",
        [
            "sport", "fitness", "exercise", "gym", "outdoor", "cycling",
            "cricket", "football", "badminton", "yoga", "cycle",
        ],
    ),
    (
        "Books & Media",
        [
            "book", "ebook", "novel", "stationery", "pen", "education",
            "learning", "media", "music", "movie",
        ],
    ),
    (
        "Toys & Kids",
        [
            "toy", "baby", "infant", "kids", "child", "game", "puzzle",
            "doll", "stroller",
        ],
    ),
    (
        "Grocery & Food",
        [
            "grocery", "food", "beverage", "snack", "gourmet", "organic",
            "spice", "oil", "tea", "coffee",
        ],
    ),
    (
        "Automotive",
        [
            "automotive", "car", "bike", "vehicle", "motor", "tyre",
            "tire", "helmet", "automobile",
        ],
    ),
]

# Direct map for common first-level marketplace labels
_DIRECT_MAP = {
    "electronics": "Electronics",
    "electronic": "Electronics",
    "clothing": "Fashion",
    "fashion": "Fashion",
    "apparel": "Fashion",
    "furniture": "Home & Furniture",
    "home": "Home & Furniture",
    "kitchen": "Home & Furniture",
    "beauty": "Beauty & Personal Care",
    "personal care": "Beauty & Personal Care",
    "sports": "Sports & Fitness",
    "sporting": "Sports & Fitness",
    "books": "Books & Media",
    "toys": "Toys & Kids",
    "baby": "Toys & Kids",
    "grocery": "Grocery & Food",
    "food": "Grocery & Food",
    "automotive": "Automotive",
    "others": "Others",
    "other": "Others",
}


def clean_raw_category(raw_category):
    """Normalize marketplace category strings from CSV."""
    if raw_category is None or str(raw_category).strip().lower() in ("", "nan", "none"):
        return ""

    raw = str(raw_category)
    raw = raw.replace("[", "").replace("]", "")
    raw = raw.replace('"', "").replace("'", "")
    parts = raw.split(">>")
    return parts[0].strip()[:120]


def classify_product(raw_category, product_name=""):
    """
    Return one of STANDARD_CATEGORIES for a product.
    Uses raw category path and product name keywords.
    """
    main = clean_raw_category(raw_category)
    name = (product_name or "").strip()
    blob = f"{main} {name}".lower()
    blob = re.sub(r"\s+", " ", blob)

    main_lower = main.lower().strip()
    if main_lower in _DIRECT_MAP:
        return _DIRECT_MAP[main_lower]

    for standard, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw in blob:
                return standard

    if main:
        # Partial match on first word of category
        first = main_lower.split()[0] if main_lower else ""
        if first in _DIRECT_MAP:
            return _DIRECT_MAP[first]

    return "Others"


def get_standard_category(raw_category, product_name="", category_model=None):
    """
    Get or create Django Category for the classified standard name.
    category_model is cart.models.Category (passed to avoid circular imports).
    """
    if category_model is None:
        from cart.models import Category
        category_model = Category

    standard_name = classify_product(raw_category, product_name)
    category, _ = category_model.objects.get_or_create(name=standard_name)
    return category


def ensure_standard_categories(category_model=None):
    """Create all standard category rows if missing."""
    if category_model is None:
        from cart.models import Category
        category_model = Category

    for name in STANDARD_CATEGORIES:
        category_model.objects.get_or_create(name=name)
