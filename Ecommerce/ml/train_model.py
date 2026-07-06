import os
import sys
import django
import random
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# =========================================
# DJANGO SETUP
# =========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "Ecommerce.settings"
)

django.setup()

# =========================================
# IMPORT MODELS
# =========================================

from cart.models import Product, PriceHistory

# =========================================
# TRAINING DATA
# =========================================

training_data = []

products = Product.objects.all()

print("TOTAL PRODUCTS:", products.count())

# =========================================
# LOOP PRODUCTS
# =========================================

for product in products:

    try:

        print("CHECKING:", product.name)

        if not product.price:

            print("NO PRICE")
            continue

        history = PriceHistory.objects.filter(
            product=product
        ).order_by('date')

        history_prices = list(
            history.values_list(
                'price',
                flat=True
            )
        )

        print("HISTORY COUNT:", len(history_prices))

        if len(history_prices) < 10:

            print("LESS THAN 10")
            continue

        # KEEP LAST 10
        history_prices = history_prices[-10:]

        history_prices = [
            float(p)
            for p in history_prices
        ]

        current_price = float(product.price)

        rating = float(product.rating or 0)

        # =====================================
        # FEATURE ENGINEERING
        # =====================================

        avg_price = sum(history_prices) / len(history_prices)

        max_price = max(history_prices)

        min_price = min(history_prices)

        volatility = max_price - min_price

        trend = history_prices[-1] - history_prices[0]

        trend_percent = (
            trend / history_prices[0]
            if history_prices[0] != 0
            else 0
        )

        # =====================================
        # FUTURE PRICE
        # =====================================

        if trend > 0:

            future_price = current_price + random.uniform(
                0,
                current_price * 0.12
            )

        else:

            future_price = current_price - random.uniform(
                0,
                current_price * 0.10
            )

        future_price += (
            avg_price - current_price
        ) * 0.1

        # =====================================
        # CREATE ROW
        # =====================================

        row = {

            "current_price": current_price,

            "rating": rating,

            "price_day_1": history_prices[0],
            "price_day_2": history_prices[1],
            "price_day_3": history_prices[2],
            "price_day_4": history_prices[3],
            "price_day_5": history_prices[4],
            "price_day_6": history_prices[5],
            "price_day_7": history_prices[6],
            "price_day_8": history_prices[7],
            "price_day_9": history_prices[8],
            "price_day_10": history_prices[9],

            "avg_price": avg_price,
            "max_price": max_price,
            "min_price": min_price,
            "volatility": volatility,
            "trend": trend,
            "trend_percent": trend_percent,

            "future_price": future_price
        }

        training_data.append(row)

        print("ADDED")

    except Exception as e:

        print("ERROR:", e)

# =========================================
# DATAFRAME
# =========================================

df = pd.DataFrame(training_data)

print("===================================")
print("TOTAL TRAINING ROWS:", len(df))
print("===================================")

if df.empty:

    print("NO TRAINING DATA FOUND")
    exit()

print(df.head())

# =========================================
# FEATURES & TARGET
# =========================================

X = df.drop(
    "future_price",
    axis=1
)

y = df["future_price"]

print("===================================")
print("FEATURE COLUMNS:")
print(X.columns)
print("===================================")

# =========================================
# EVALUATE MODEL
# =========================================

print("EVALUATING MODEL ACCURACY...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)
y_pred = model.predict(X_test)

r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print(f"Model Accuracy (R^2 Score): {r2:.4f}")
print(f"Mean Absolute Error: {mae:.2f}")
print("===================================")

# =========================================
# TRAIN FINAL MODEL ON ALL DATA
# =========================================

print("TRAINING FINAL MODEL ON ALL DATA...")

model.fit(X, y)

print("MODEL TRAINED")

# =========================================
# SAVE MODEL
# =========================================

MODEL_DIR = os.path.dirname(__file__)

joblib.dump(
    model,
    os.path.join(
        MODEL_DIR,
        "price_prediction_model.pkl"
    )
)

joblib.dump(
    list(X.columns),
    os.path.join(
        MODEL_DIR,
        "model_features.pkl"
    )
)

print("===================================")
print("MODEL FILE SAVED")
print("FEATURE FILE SAVED")
print("===================================")