import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent

# Outputs
COMPARISON_CSV = ROOT / "opticart_comparison_dataset.csv"
AMAZON_CSV = ROOT / "fixed_amazon_dataset_new.csv"
FLIPKART_CSV = ROOT / "fixed_flipkart_dataset_new.csv"

# 5000 products (each exists on both platforms)
N_PRODUCTS = 5000

CATEGORIES = {
    "Mobiles": {
        "price_range": (6999, 119999),
        "brands": ["Samsung", "Apple", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola"],
        "name_templates": [
            "{brand} {series} {ram}GB/{storage}GB {tag}",
            "{brand} {series} ({storage}GB) {tag}",
        ],
        "series": ["Galaxy M", "Galaxy A", "iPhone", "Nord", "Redmi Note", "Narzo", "V", "Reno", "Moto G"],
        "tags": ["5G", "AMOLED", "Fast Charge", "Dual SIM", "AI Camera", "120Hz"],
    },
    "Laptops": {
        "price_range": (28999, 129999),
        "brands": ["Dell", "HP", "Lenovo", "Asus", "Acer", "Apple", "MSI"],
        "name_templates": [
            "{brand} {series} {cpu} {ram}GB {storage}GB {screen}\"",
            "{brand} {series} {cpu} {ram}GB/{storage}GB {tag}",
        ],
        "series": ["Inspiron", "Pavilion", "IdeaPad", "VivoBook", "Aspire", "MacBook Air", "Katana"],
        "cpus": ["i5", "i7", "Ryzen 5", "Ryzen 7", "M2", "M3"],
        "tags": ["SSD", "Office", "Gaming", "Student"],
    },
    "Fashion": {
        "price_range": (199, 14999),
        "brands": ["Puma", "Nike", "Adidas", "Levi's", "Allen Solly", "H&M", "BIBA", "Roadster"],
        "name_templates": [
            "{brand} {item} {fit} {material}",
            "{brand} {item} {tag}",
        ],
        "items": ["T-Shirt", "Jeans", "Sneakers", "Jacket", "Kurta", "Dress", "Backpack", "Watch"],
        "fits": ["Slim Fit", "Regular", "Oversized", "Skinny"],
        "materials": ["Cotton", "Denim", "Polyester", "Linen"],
        "tags": ["Casual", "Formal", "Sports", "Ethnic"],
    },
    "Electronics": {
        "price_range": (399, 69999),
        "brands": ["Sony", "JBL", "boAt", "Philips", "LG", "Samsung", "Mi"],
        "name_templates": [
            "{brand} {item} {tag}",
            "{brand} {item} {model} {tag}",
        ],
        "items": ["Bluetooth Speaker", "Headphones", "Soundbar", "Smart TV", "Monitor", "Toner Cartridge"],
        "tags": ["Wireless", "Dolby", "Noise Cancel", "4K", "HDR", "Bass Boost"],
    },
    "Home Appliances": {
        "price_range": (1499, 99999),
        "brands": ["LG", "Samsung", "Whirlpool", "Bosch", "IFB", "Godrej", "Haier"],
        "name_templates": [
            "{brand} {item} {capacity} {tag}",
            "{brand} {item} {tag}",
        ],
        "items": ["Washing Machine", "Refrigerator", "Microwave", "Air Conditioner", "Water Purifier"],
        "tags": ["Inverter", "Energy Efficient", "Frost Free", "Front Load", "5 Star"],
    },
    "Books": {
        "price_range": (99, 1999),
        "brands": ["Penguin", "HarperCollins", "Bloomsbury", "Scholastic", "Oxford"],
        "name_templates": [
            "{title} ({tag})",
            "{title} - {tag}",
        ],
        "titles": [
            "Atomic Habits",
            "The Psychology of Money",
            "Ikigai",
            "The Alchemist",
            "Rich Dad Poor Dad",
            "Sapiens",
            "Deep Work",
        ],
        "tags": ["Paperback", "Hardcover", "Bestseller", "Self-Help", "Fiction", "Non-Fiction"],
    },
    "Beauty": {
        "price_range": (149, 4999),
        "brands": ["Lakme", "Maybelline", "Nykaa", "L'Oréal", "Mamaearth", "Nivea"],
        "name_templates": [
            "{brand} {item} {tag}",
            "{brand} {item} ({tag})",
        ],
        "items": ["Face Wash", "Moisturizer", "Lipstick", "Serum", "Sunscreen", "Shampoo"],
        "tags": ["Matte", "SPF 50", "Vitamin C", "Paraben Free", "Long Lasting"],
    },
    "Furniture": {
        "price_range": (1999, 99999),
        "brands": ["Pepperfry", "Urban Ladder", "IKEA", "HomeTown", "Nilkamal"],
        "name_templates": [
            "{brand} {item} {material} {tag}",
            "{brand} {item} {tag}",
        ],
        "items": ["Office Chair", "Sofa", "Dining Table", "Bed", "Wardrobe", "TV Unit"],
        "materials": ["Engineered Wood", "Sheesham", "Metal", "Fabric"],
        "tags": ["Ergonomic", "Compact", "3-Seater", "Storage"],
    },
    "Gaming": {
        "price_range": (599, 99999),
        "brands": ["Sony", "Microsoft", "Nintendo", "Logitech", "Razer", "Asus", "MSI"],
        "name_templates": [
            "{brand} {item} {tag}",
            "{brand} {item} {model} {tag}",
        ],
        "items": ["Gaming Console", "Controller", "Mechanical Keyboard", "Gaming Mouse", "Gaming Headset"],
        "tags": ["RGB", "4K", "120FPS", "Wireless", "Pro"],
    },
    "Groceries": {
        "price_range": (39, 2999),
        "brands": ["Aashirvaad", "Fortune", "Tata", "Amul", "Nestle", "Patanjali"],
        "name_templates": [
            "{brand} {item} {pack}",
            "{brand} {item} ({pack})",
        ],
        "items": ["Atta", "Rice", "Tea", "Coffee", "Cooking Oil", "Biscuits", "Ghee"],
        "packs": ["1kg", "2kg", "5kg", "500g", "1L", "2L"],
    },
}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def rupee_price(low, high):
    base = random.uniform(low, high)
    # Common retail endings
    ending = random.choice([0, 9, 49, 99])
    rounded = round(base / 10) * 10
    price = rounded + ending
    return float(max(1, price))


def rating():
    # More realistic skew: many 3.8-4.6, few extremes
    r = random.gauss(4.2, 0.45)
    return round(clamp(r, 2.5, 5.0), 1)


def reviews_for(category):
    if category in ("Mobiles", "Laptops", "Electronics", "Gaming"):
        return random.randint(80, 25000)
    if category in ("Fashion", "Home Appliances", "Furniture", "Beauty"):
        return random.randint(30, 15000)
    return random.randint(10, 8000)


def delivery_days(category):
    if category in ("Mobiles", "Laptops", "Electronics", "Beauty", "Books"):
        return random.randint(1, 5)
    if category == "Groceries":
        return random.randint(1, 3)
    return random.randint(2, 10)


def stock_status():
    p = random.random()
    if p < 0.82:
        return "In Stock"
    if p < 0.95:
        return "Limited Stock"
    return "Out of Stock"


def build_name(category, brand):
    cfg = CATEGORIES[category]
    # Keep brand-model combinations realistic for key categories.
    if category == "Mobiles":
        series_by_brand = {
            "Apple": ["iPhone 13", "iPhone 14", "iPhone 15"],
            "Samsung": ["Galaxy M14", "Galaxy A35", "Galaxy S23 FE"],
            "OnePlus": ["Nord CE 4", "11R", "12R"],
            "Xiaomi": ["Redmi Note 13", "Redmi 13C", "Xiaomi 14"],
            "Realme": ["Narzo 70", "11 Pro", "P1"],
            "Vivo": ["T3", "Y200", "V30"],
            "Oppo": ["Reno 11", "A79", "F25 Pro"],
            "Motorola": ["Moto G54", "Edge 50", "Moto G84"],
        }
        model = random.choice(series_by_brand.get(brand, ["Smartphone"]))
        storage = random.choice([64, 128, 256, 512])
        ram = random.choice([4, 6, 8, 12])
        tag = random.choice(cfg["tags"])
        return f"{brand} {model} {ram}GB/{storage}GB {tag}"

    if category == "Laptops":
        series_by_brand = {
            "Dell": ["Inspiron 15", "Vostro 14", "G15"],
            "HP": ["Pavilion 15", "Victus 16", "14s"],
            "Lenovo": ["IdeaPad Slim 3", "LOQ 15", "ThinkBook 14"],
            "Asus": ["VivoBook 15", "TUF F15", "Zenbook 14"],
            "Acer": ["Aspire 7", "Nitro V", "Swift Go 14"],
            "Apple": ["MacBook Air M2", "MacBook Air M3"],
            "MSI": ["Katana 15", "Thin GF63"],
        }
        model = random.choice(series_by_brand.get(brand, ["Laptop"]))
        cpu = random.choice(["i5", "i7", "Ryzen 5", "Ryzen 7", "M2", "M3"])
        ram = random.choice([8, 16, 32])
        storage = random.choice([256, 512, 1024])
        return f"{brand} {model} {cpu} {ram}GB/{storage}GB"

    tmpl = random.choice(cfg["name_templates"])
    kw = random.choice(cfg.get("tags", cfg.get("keywords", ["Premium"])))
    series = random.choice(cfg.get("series", ["Series"]))
    cpu = random.choice(cfg.get("cpus", ["i5"]))
    item = random.choice(cfg.get("items", ["Product"]))
    fit = random.choice(cfg.get("fits", ["Regular"]))
    material = random.choice(cfg.get("materials", ["Cotton"]))
    storage = random.choice([64, 128, 256, 512, 1024])
    ram = random.choice([4, 6, 8, 12, 16, 32])
    screen = random.choice([13.3, 14, 15.6, 16])
    capacity = random.choice(["7kg", "8kg", "9kg", "190L", "260L", "1.5 Ton", "2 Ton"])
    title = random.choice(cfg.get("titles", ["OptiCart Picks"]))
    pack = random.choice(cfg.get("packs", ["1kg"]))
    model = str(random.randint(100, 9999))
    return tmpl.format(
        brand=brand,
        series=series,
        cpu=cpu,
        item=item,
        fit=fit,
        material=material,
        tag=kw,
        storage=storage,
        ram=ram,
        screen=screen,
        capacity=capacity,
        title=title,
        pack=pack,
        model=model,
    ).replace("  ", " ").strip()


def history_prices(base_price):
    # 10-day history with drift + noise
    prices = []
    p = base_price * random.uniform(0.96, 1.04)
    drift = random.choice([-1, 0, 1]) * random.uniform(0.001, 0.006)
    for _ in range(10):
        shock = random.gauss(0, 0.015)  # ~1.5% noise
        p = p * (1 + drift + shock)
        p = max(1.0, p)
        prices.append(round(p, 2))
    return prices


def future_prediction_from_history(hist):
    first, last = hist[0], hist[-1]
    if first <= 0:
        return last, "STABLE"
    pct = (last - first) / first
    if pct > 0.04:
        trend = "UP"
    elif pct < -0.04:
        trend = "DOWN"
    else:
        trend = "STABLE"
    # Predict modest continuation with damping
    future = last * (1 + pct * 0.5 + random.gauss(0, 0.01))
    return round(max(1.0, future), 2), trend


def ai_decision(lowest, future, discount_pct, stock):
    drop_pct = (lowest - future) / lowest if lowest else 0
    if stock == "Out of Stock":
        return 35, "WAIT"
    if drop_pct > 0.07:
        return random.randint(60, 80), "PRICE MAY DROP"
    if discount_pct >= 18 and drop_pct < 0.03:
        return random.randint(80, 95), "BUY NOW"
    return random.randint(50, 70), "WAIT"


def popularity(category):
    if category in ("Mobiles", "Laptops", "Electronics", "Gaming"):
        pop = random.randint(70, 100)
        search = random.randint(8000, 250000)
    elif category in ("Fashion", "Home Appliances", "Furniture", "Beauty"):
        pop = random.randint(55, 95)
        search = random.randint(4000, 120000)
    else:
        pop = random.randint(45, 90)
        search = random.randint(2000, 80000)
    purchase = int(search * random.uniform(0.04, 0.25))
    return pop, search, purchase


def image_url(product_id, category, product_name):
    # Keep dataset images aligned with product type.
    # Import from project module while running script from datasets/.
    import sys

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.append(str(PROJECT_ROOT))

    from cart.image_mapping import image_url_seed_for_row

    return image_url_seed_for_row(product_id, product_name, category)


def url_for(platform, product_id):
    if platform == "Amazon":
        return f"https://www.amazon.in/dp/OPT{product_id:06d}?tag=opticart"
    return f"https://www.flipkart.com/item/OPT{product_id:06d}?pid=opticart"


def description(category, brand, name):
    return (
        f"{name} by {brand}. "
        f"Category: {category}. "
        f"Optimized for Indian pricing and delivery. "
        f"Suitable for price comparison, trend analysis, and recommendations."
    )


def write_datasets():
    random.seed(42)
    now = datetime.now()

    comparison_fields = [
        "product_id",
        "product_name",
        "category",
        "brand",
        "amazon_price",
        "flipkart_price",
        "lowest_price",
        "amazon_rating",
        "flipkart_rating",
        "amazon_reviews",
        "flipkart_reviews",
        "delivery_days_amazon",
        "delivery_days_flipkart",
        "stock_status",
        "image_url",
        "amazon_url",
        "flipkart_url",
        "description",
        "ai_score",
        "ai_recommendation",
        "future_price_prediction",
        "discount_percentage",
        "price_day_1",
        "price_day_2",
        "price_day_3",
        "price_day_4",
        "price_day_5",
        "price_day_6",
        "price_day_7",
        "price_day_8",
        "price_day_9",
        "price_day_10",
        "trend",
        "popularity_score",
        "search_count",
        "purchase_count",
        "last_updated",
    ]

    # Your Django importer expects these legacy files/columns.
    legacy_fields = [
        "product_name",
        "category",
        "current_price",
        "rating",
        "image_url",
        "product_url",
        "description",
        "platform",
        "price_day_1",
        "price_day_2",
        "price_day_3",
        "price_day_4",
        "price_day_5",
        "price_day_6",
        "price_day_7",
        "price_day_8",
        "price_day_9",
        "price_day_10",
        "future_price",
    ]

    COMPARISON_CSV.parent.mkdir(parents=True, exist_ok=True)

    with (
        open(COMPARISON_CSV, "w", newline="", encoding="utf-8") as f_cmp,
        open(AMAZON_CSV, "w", newline="", encoding="utf-8") as f_amz,
        open(FLIPKART_CSV, "w", newline="", encoding="utf-8") as f_flp,
    ):
        w_cmp = csv.DictWriter(f_cmp, fieldnames=comparison_fields)
        w_amz = csv.DictWriter(f_amz, fieldnames=legacy_fields)
        w_flp = csv.DictWriter(f_flp, fieldnames=legacy_fields)
        w_cmp.writeheader()
        w_amz.writeheader()
        w_flp.writeheader()

        categories = list(CATEGORIES.keys())

        for pid in range(1, N_PRODUCTS + 1):
            category = categories[(pid - 1) % len(categories)]
            cfg = CATEGORIES[category]
            brand = random.choice(cfg["brands"])

            # Ensure uniqueness across the entire dataset so Django import doesn't skip rows.
            name = f"{build_name(category, brand)} (OPT{pid:06d})"
            low, high = cfg["price_range"]
            base = rupee_price(low, high)

            # Platform different pricing
            amazon_price = round(base * random.uniform(0.95, 1.06), 2)
            flipkart_price = round(base * random.uniform(0.93, 1.09), 2)
            lowest = min(amazon_price, flipkart_price)

            hist = history_prices(lowest)
            future, trend = future_prediction_from_history(hist)

            peak = max(hist + [amazon_price, flipkart_price])
            discount_pct = 0.0 if peak <= 0 else max(0.0, (peak - lowest) / peak * 100)

            stock = stock_status()
            ai_score, ai_rec = ai_decision(lowest, future, discount_pct, stock)

            pop, search, purchase = popularity(category)

            last_updated = (now - timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d %H:%M:%S")

            row_cmp = {
                "product_id": f"OPT-{pid:06d}",
                "product_name": name,
                "category": category,
                "brand": brand,
                "amazon_price": amazon_price,
                "flipkart_price": flipkart_price,
                "lowest_price": round(lowest, 2),
                "amazon_rating": rating(),
                "flipkart_rating": rating(),
                "amazon_reviews": reviews_for(category),
                "flipkart_reviews": int(reviews_for(category) * random.uniform(0.7, 1.4)),
                "delivery_days_amazon": delivery_days(category),
                "delivery_days_flipkart": delivery_days(category),
                "stock_status": stock,
                "image_url": image_url(pid, category, name),
                "amazon_url": url_for("Amazon", pid),
                "flipkart_url": url_for("Flipkart", pid),
                "description": description(category, brand, name),
                "ai_score": ai_score,
                "ai_recommendation": ai_rec,
                "future_price_prediction": future,
                "discount_percentage": round(discount_pct, 2),
                "price_day_1": hist[0],
                "price_day_2": hist[1],
                "price_day_3": hist[2],
                "price_day_4": hist[3],
                "price_day_5": hist[4],
                "price_day_6": hist[5],
                "price_day_7": hist[6],
                "price_day_8": hist[7],
                "price_day_9": hist[8],
                "price_day_10": hist[9],
                "trend": trend,
                "popularity_score": pop,
                "search_count": search,
                "purchase_count": purchase,
                "last_updated": last_updated,
            }
            w_cmp.writerow(row_cmp)

            # Legacy rows for Django import pipeline (one row per platform)
            amz_hist = history_prices(amazon_price)
            flp_hist = history_prices(flipkart_price)
            amz_future, _ = future_prediction_from_history(amz_hist)
            flp_future, _ = future_prediction_from_history(flp_hist)

            row_amz = {
                "product_name": name,
                "category": category,
                "current_price": amazon_price,
                "rating": row_cmp["amazon_rating"],
                "image_url": row_cmp["image_url"],
                "product_url": row_cmp["amazon_url"],
                "description": row_cmp["description"],
                "platform": "Amazon",
                "price_day_1": amz_hist[0],
                "price_day_2": amz_hist[1],
                "price_day_3": amz_hist[2],
                "price_day_4": amz_hist[3],
                "price_day_5": amz_hist[4],
                "price_day_6": amz_hist[5],
                "price_day_7": amz_hist[6],
                "price_day_8": amz_hist[7],
                "price_day_9": amz_hist[8],
                "price_day_10": amz_hist[9],
                "future_price": amz_future,
            }
            row_flp = {
                "product_name": name,
                "category": category,
                "current_price": flipkart_price,
                "rating": row_cmp["flipkart_rating"],
                "image_url": row_cmp["image_url"],
                "product_url": row_cmp["flipkart_url"],
                "description": row_cmp["description"],
                "platform": "Flipkart",
                "price_day_1": flp_hist[0],
                "price_day_2": flp_hist[1],
                "price_day_3": flp_hist[2],
                "price_day_4": flp_hist[3],
                "price_day_5": flp_hist[4],
                "price_day_6": flp_hist[5],
                "price_day_7": flp_hist[6],
                "price_day_8": flp_hist[7],
                "price_day_9": flp_hist[8],
                "price_day_10": flp_hist[9],
                "future_price": flp_future,
            }
            w_amz.writerow(row_amz)
            w_flp.writerow(row_flp)

    print("Generated:")
    print(" -", COMPARISON_CSV)
    print(" -", AMAZON_CSV)
    print(" -", FLIPKART_CSV)


if __name__ == "__main__":
    write_datasets()

