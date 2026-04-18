# ================================================================
# AutoShield — Model Utilities
# Handles all ML model loading, preprocessing, and prediction.
# ================================================================

import os, io, logging
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

logger = logging.getLogger("autoshield.model_utils")

# ----------------------------------------------------------------
# PATHS — resolve relative to project root
# ----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models"
DATA_DIR  = ROOT / "data"

NUMERIC_MODEL_PATH = MODEL_DIR / "car_claim_numeric_model.pkl"
IMAGE_MODEL_PATH   = MODEL_DIR / "best_image_model.pth"
TRAIN_CSV_PATH     = DATA_DIR  / "train.csv"

# ----------------------------------------------------------------
# MODULE-LEVEL SINGLETONS (loaded once at startup)
# ----------------------------------------------------------------
_numeric_model = None
_image_model   = None
_train_template = None   # single-row template for feature alignment


# ================================================================
# LOADERS
# ================================================================

def _load_numeric_model():
    global _numeric_model
    if _numeric_model is not None:
        return _numeric_model
    if not NUMERIC_MODEL_PATH.exists():
        raise FileNotFoundError(f"Numeric model not found at {NUMERIC_MODEL_PATH}")
    _numeric_model = joblib.load(NUMERIC_MODEL_PATH)
    logger.info("✅ Numeric model loaded")
    return _numeric_model


def _load_train_template() -> pd.DataFrame:
    """
    Load a single-row template from train.csv for column alignment.
    Cached after first load.
    """
    global _train_template
    if _train_template is not None:
        return _train_template

    if not TRAIN_CSV_PATH.exists():
        raise FileNotFoundError(f"train.csv not found at {TRAIN_CSV_PATH}")

    df = pd.read_csv(TRAIN_CSV_PATH, nrows=1)
    df = df.drop(columns=["is_claim"], errors="ignore")

    # --- Fix string columns that contain units ---
    for col in ["max_power", "max_torque"]:
        if col in df.columns:
            df[col] = df[col].apply(_extract_number)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["gross_weight", "displacement", "cylinder", "gear_box",
                "turning_radius", "length", "width", "height"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    _train_template = df
    logger.info("✅ Train template loaded")
    return _train_template


def _load_image_model():
    global _image_model
    if _image_model is not None:
        return _image_model

    if not IMAGE_MODEL_PATH.exists():
        logger.warning("⚠️  Image model (.pth) not found — image prediction disabled")
        return None

    try:
        import torch
        import torch.nn as nn
        import torchvision

        device = torch.device("cpu")
        model = torchvision.models.alexnet(weights=None)
        model.classifier[6] = nn.Linear(4096, 2)
        model.load_state_dict(torch.load(IMAGE_MODEL_PATH, map_location=device))
        model.eval()
        _image_model = model
        logger.info("✅ Image model loaded")
        return _image_model
    except Exception as e:
        logger.error(f"Failed to load image model: {e}")
        return None


# ================================================================
# HELPERS
# ================================================================

def _extract_number(x):
    """Extract first numeric token from strings like '88.50bhp@6000rpm'."""
    try:
        return float(str(x).split()[0].split("b")[0].split("N")[0])
    except Exception:
        return np.nan


FUEL_MAP = {"Petrol": "Petrol", "Diesel": "Diesel", "CNG": "CNG"}


# ================================================================
# PREDICTION FUNCTIONS
# ================================================================

def predict_claim_numeric(payload) -> "NumericPredictionResponse":
    """
    Build feature-consistent input from ClaimInput and run the
    trained XGBoost pipeline.
    """
    from backend.schemas import NumericPredictionResponse

    model    = _load_numeric_model()
    template = _load_train_template().copy()

    # --- Inject user values ---
    template["age_of_policyholder"] = float(payload.age_of_policyholder)
    template["age_of_car"]          = float(payload.age_of_car)
    template["airbags"]             = int(payload.airbags)
    template["ncap_rating"]         = int(payload.ncap_rating)
    template["policy_tenure"]       = float(payload.policy_tenure)

    fuel = FUEL_MAP.get(payload.fuel_type, "Petrol")
    if "fuel_type" in template.columns:
        template["fuel_type"] = fuel

    # --- Feature engineering (must match training) ---
    max_power_val    = pd.to_numeric(template.get("max_power",   [np.nan]).values[0], errors="coerce")
    gross_weight_val = pd.to_numeric(template.get("gross_weight",[np.nan]).values[0], errors="coerce")

    if pd.isna(max_power_val):
        max_power_val = 80.0          # sensible default
    if pd.isna(gross_weight_val):
        gross_weight_val = 1200.0

    template["engine_per_weight"] = max_power_val / (gross_weight_val + 1)
    template["age_ratio"] = payload.age_of_car / (payload.age_of_policyholder + 1)

    # --- Fill remaining NaNs ---
    template = template.fillna(0)

    # --- Predict ---
    claim_prob   = float(model.predict_proba(template)[:, 1][0])
    approval_prob = round(1 - claim_prob, 4)
    claim_prob    = round(claim_prob, 4)

    # --- Risk logic ---
    if claim_prob < 0.30:
        risk_level, approval_likelihood, decision = "Low Risk", "High", "Auto Approve"
        explanation = "Your profile looks safe. Claim is likely to be approved quickly."
    elif claim_prob < 0.60:
        risk_level, approval_likelihood, decision = "Medium Risk", "Moderate", "Manual Review"
        explanation = "Some risk detected. Your claim may require manual verification."
    else:
        risk_level, approval_likelihood, decision = "High Risk", "Low", "Investigate"
        explanation = "High risk detected. Claim may be delayed or flagged for investigation."

    return NumericPredictionResponse(
        claim_probability=claim_prob,
        approval_probability=approval_prob,
        risk_level=risk_level,
        approval_likelihood=approval_likelihood,
        decision=decision,
        explanation=explanation,
    )


def predict_image_fraud(image_bytes: bytes) -> dict:
    """
    Run AlexNet fraud-detection on raw image bytes.
    Returns label, confidence, and a flag if model is unavailable.
    """
    model = _load_image_model()
    if model is None:
        return {
            "label": "Unavailable",
            "confidence": 0.0,
            "note": "Image model not loaded — place best_image_model.pth in /models/",
        }

    try:
        import torch
        import torchvision.transforms as T
        from PIL import Image

        transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize([0.5] * 3, [0.5] * 3),
        ])

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = model(tensor)
            probs  = torch.softmax(output, dim=1)
            pred   = torch.argmax(probs, 1).item()
            conf   = float(probs[0][pred].item())

        classes = ["Normal", "Suspicious"]
        label   = "Uncertain" if conf < 0.60 else classes[pred]

        return {"label": label, "confidence": round(conf, 4)}

    except Exception as e:
        logger.exception("Image prediction runtime error")
        return {"label": "Error", "confidence": 0.0, "note": str(e)}


def get_model_info() -> dict:
    """Return which models are currently loaded (for /health endpoint)."""
    numeric_ok = NUMERIC_MODEL_PATH.exists()
    image_ok   = IMAGE_MODEL_PATH.exists()
    return {
        "numeric_model_loaded": numeric_ok,
        "image_model_loaded": image_ok,
    }
