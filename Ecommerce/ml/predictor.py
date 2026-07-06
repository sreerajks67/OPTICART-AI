import os
import joblib
import pandas as pd

# =====================================
# BASE DIRECTORY
# =====================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# =====================================
# FILE PATHS
# =====================================

model_path = os.path.join(
    BASE_DIR,
    "price_prediction_model.pkl"
)

feature_path = os.path.join(
    BASE_DIR,
    "model_features.pkl"
)

# =====================================
# PRICE PREDICTION
# =====================================

def predict_price(product_data):

    try:

        # =====================================
        # CHECK FILES EXIST
        # =====================================

        if not os.path.exists(model_path):

            print("MODEL FILE NOT FOUND")

            return float(
                product_data["current_price"]
            )

        if not os.path.exists(feature_path):

            print("FEATURE FILE NOT FOUND")

            return float(
                product_data["current_price"]
            )

        # =====================================
        # LOAD MODEL
        # =====================================

        model = joblib.load(model_path)

        feature_columns = joblib.load(feature_path)

        # =====================================
        # CREATE INPUT DATA
        # =====================================

        data = {}

        for col in feature_columns:

            data[col] = product_data.get(col, 0)

        df = pd.DataFrame([data])

        # =====================================
        # PREDICT
        # =====================================

        prediction = model.predict(df)[0]

        prediction = round(
            float(prediction),
            2
        )

        # =====================================
        # SAFETY CHECK
        # =====================================

        current_price = float(
            product_data["current_price"]
        )

        # Prevent impossible values
        if prediction <= 0:

            prediction = current_price

        # Limit extreme jumps
        max_allowed = current_price * 1.5
        min_allowed = current_price * 0.5

        prediction = max(
            min_allowed,
            min(prediction, max_allowed)
        )

        return round(prediction, 2)

    except Exception as e:

        print("===================================")
        print("PREDICTION ERROR")
        print(e)
        print("===================================")

        return float(
            product_data["current_price"]
        )