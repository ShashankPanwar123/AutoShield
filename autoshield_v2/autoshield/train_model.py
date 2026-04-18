#!/usr/bin/env python3
# ================================================================
# AutoShield — Model Training Script  (run once to produce .pkl)
# Usage: python train_model.py
# Output: models/car_claim_numeric_model.pkl
# ================================================================

import sys, time, logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score

from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("train")

# ----------------------------------------------------------------
# PATHS
# ----------------------------------------------------------------
ROOT      = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "train.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)
OUT_PATH  = MODEL_DIR / "car_claim_numeric_model.pkl"


# ----------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------
def extract_number(x):
    """Extract first numeric token from strings like '88.50bhp@6000rpm'."""
    try:
        val = str(x).split()[0]
        # strip any trailing non-numeric chars character-by-character
        num = ""
        for ch in val:
            if ch in "0123456789.":
                num += ch
            elif num:
                break
        return float(num)
    except Exception:
        return np.nan


# ================================================================
# MAIN
# ================================================================
def main():
    t0 = time.time()

    # ---- Load ----
    log.info(f"Loading data from {DATA_PATH}")
    if not DATA_PATH.exists():
        log.error("train.csv not found. Place it in the /data/ directory.")
        sys.exit(1)

    df = pd.read_csv(DATA_PATH)
    log.info(f"Shape: {df.shape}  |  Claim rate: {df['is_claim'].mean():.2%}")

    # ---- Drop ID ----
    df.drop(columns=["policy_id"], errors="ignore", inplace=True)

    # ---- Fix numeric strings ----
    for col in ["max_power", "max_torque"]:
        if col in df.columns:
            df[col] = df[col].apply(extract_number)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["gross_weight", "displacement", "cylinder", "gear_box",
                "turning_radius", "length", "width", "height"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ---- Feature engineering ----
    df["engine_per_weight"] = df["max_power"] / (df["gross_weight"] + 1)
    df["age_ratio"]         = df["age_of_car"] / (df["age_of_policyholder"] + 1)

    # ---- Split X / y ----
    TARGET = "is_claim"
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    log.info(f"Numeric features: {len(num_cols)}  |  Categorical features: {len(cat_cols)}")

    # ---- Preprocessing ----
    num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols),
    ])

    # ---- Train / Val split ----
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scale_pos_weight = len(y_train[y_train == 0]) / max(len(y_train[y_train == 1]), 1)
    log.info(f"scale_pos_weight = {scale_pos_weight:.2f}")

    # ---- Pipeline with SMOTE + XGBoost ----
    pipeline = ImbPipeline([
        ("preprocessor", preprocessor),
        ("smote", SMOTE(random_state=42, k_neighbors=3)),
        ("model", XGBClassifier(
            n_estimators=500,
            learning_rate=0.03,
            max_depth=8,
            min_child_weight=3,
            subsample=0.9,
            colsample_bytree=0.9,
            gamma=0.2,
            reg_alpha=0.5,
            reg_lambda=1.5,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            n_jobs=-1,
            eval_metric="logloss",
            verbosity=0,
        )),
    ])

    log.info("Training …")
    pipeline.fit(X_train, y_train)

    # ---- Evaluate ----
    y_pred  = pipeline.predict(X_val)
    y_proba = pipeline.predict_proba(X_val)[:, 1]

    auc = roc_auc_score(y_val, y_proba)
    log.info(f"\n{classification_report(y_val, y_pred)}")
    log.info(f"ROC-AUC: {auc:.4f}")

    # ---- Save ----
    joblib.dump(pipeline, OUT_PATH)
    log.info(f"✅ Model saved → {OUT_PATH}  ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
