"""
ml.py
=====
Reproduces the project's Random Forest regression stage.

analysis_results.xlsx (which would have held the original notebook's
test-set predictions and feature-importance table) was not among the
files uploaded for this dashboard. Rather than inventing numbers, this
module retrains the same kind of model, live, directly on data/dataset.csv,
following the methodology the report describes in section 8.2:
"a 75:25 train-test split with 300 trees and a minimum of two samples per
leaf", one separate model per vehicle type, features = speed, distance,
ambient temperature, vehicle load, traffic level (encoded).

The report's own R²/MAE/RMSE figures (Table 3) are shown alongside these
live results everywhere they appear, clearly labelled, since a different
random split will not reproduce the exact same numbers.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

FEATURES = ["speed_kmph", "distance_km", "ambient_temperature", "vehicle_load", "traffic_level_code"]
TRAFFIC_MAP = {"Low": 0, "Medium": 1, "High": 2}


def _prep(df, vehicle_type):
    sub = df[df["vehicle_type"] == vehicle_type].copy()
    sub = sub.dropna(subset=["speed_kmph", "distance_km", "ambient_temperature", "vehicle_load", "fuel_or_energy_consumption"])
    sub["traffic_level_code"] = sub["traffic_level"].map(TRAFFIC_MAP)
    return sub


def train_and_evaluate(df, vehicle_type, random_state=42):
    sub = _prep(df, vehicle_type)
    X = sub[FEATURES]
    y = sub["fuel_or_energy_consumption"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=random_state)

    model = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=random_state)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5

    importances = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)

    pred_df = pd.DataFrame({"actual": y_test.values, "predicted": y_pred})

    return {
        "r2": r2, "mae": mae, "rmse": rmse,
        "importances": importances,
        "predictions": pred_df,
        "n_train": len(X_train), "n_test": len(X_test),
    }
