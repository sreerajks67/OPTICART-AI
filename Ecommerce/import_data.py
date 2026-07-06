import os
import django
import pandas as pd
import random

# =========================================
# DJANGO SETUP
# =========================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "Ecommerce.settings"
)

django.setup()

from cart.models import (
    Product,
    Category,
    PriceHistory
)
from cart.utils import normalize_image_url
from cart.categories import get_standard_category, ensure_standard_categories
from cart.pricing import compute_prices_from_row

# =========================================
# LOAD DATASETS
# =========================================

amazon_df = pd.read_csv(
    "datasets/fixed_amazon_dataset_new.csv"
)

flipkart_df = pd.read_csv(
    "datasets/fixed_flipkart_dataset_new.csv"
)

# =========================================
# IMPORT FUNCTION
# =========================================

ensure_standard_categories()

def import_products(df, platform_name):

    count = 0

    for index, row in df.iterrows():

        try:

            # =====================================
            # PRODUCT NAME
            # =====================================

            product_name = str(
                row.get("product_name", "")
            ).strip()

            if not product_name or product_name == "nan":
                continue

            # =====================================
            # DUPLICATE CHECK
            # =====================================

            if Product.objects.filter(
                name=product_name,
                platform=platform_name
            ).exists():
                continue

            # =====================================
            # CATEGORY
            # =====================================

            category = get_standard_category(
                row.get("category", "Others"),
                product_name=product_name,
            )

            current_price, old_price, history_prices = compute_prices_from_row(row)

            # =====================================
            # RATING
            # =====================================

            try:
                rating = float(
                    row.get("rating", 0)
                )
            except:
                rating = 0

            # =====================================
            # IMAGE
            # =====================================

            image_url = normalize_image_url(
                row.get("image_url", "")
            )

            # =====================================
            # PRODUCT URL
            # =====================================

            product_url = str(
                row.get("product_url", "")
            )

            # =====================================
            # DESCRIPTION
            # =====================================

            description = str(
                row.get("description", "")
            )

            # =====================================
            # CREATE PRODUCT
            # =====================================

            product = Product.objects.create(

                name=product_name[:200],

                category=category,

                price=current_price,

                old_price=old_price,

                rating=rating,

                platform=platform_name,

                image_url=image_url,

                product_url=product_url,

                description=description,

                stock=random.randint(5, 50),

                ai_score=random.randint(40, 95),

                ai_recommendation=random.choice(
                    [
                        "Buy Now",
                        "Wait",
                        "Price Will Drop"
                    ]
                )

            )

            # =====================================
            # PRICE HISTORY
            # =====================================

            for history_price in history_prices:

                PriceHistory.objects.create(
                    product=product,
                    price=history_price,
                )

            count += 1

            print(
                f"{platform_name} Imported:",
                count
            )

        except Exception as e:

            print(
                f"{platform_name} ERROR:",
                e
            )

    return count


# =========================================
# IMPORT AMAZON
# =========================================

print("===================================")
print("Importing Amazon Products...")
print("===================================")

amazon_count = import_products(
    amazon_df,
    "Amazon"
)

# =========================================
# IMPORT FLIPKART
# =========================================

print("===================================")
print("Importing Flipkart Products...")
print("===================================")

flipkart_count = import_products(
    flipkart_df,
    "Flipkart"
)

# =========================================
# COMPLETED
# =========================================

print("===================================")
print("IMPORT COMPLETED SUCCESSFULLY")
print("===================================")

print("Amazon Products:", amazon_count)
print("Flipkart Products:", flipkart_count)