# ================================================================
# AutoShield — FastAPI Backend  v2.0
# ================================================================

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn, logging

from backend.schemas import (
    ClaimInput, NumericPredictionResponse,
    CombinedPredictionResponse, HealthResponse,
)
from backend.model_utils import predict_claim_numeric, predict_image_fraud, get_model_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autoshield")

app = FastAPI(
    title="AutoShield — Car Insurance AI API",
    description="ML-powered car insurance claim prediction & fraud detection",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------
# ROOT / HEALTH
# ----------------------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {"message": "AutoShield AI API v2.0 🚗", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    info = get_model_info()
    return HealthResponse(**info, status="ok")


# ----------------------------------------------------------------
# NUMERIC PREDICTION
# ----------------------------------------------------------------
@app.post("/predict/numeric", response_model=NumericPredictionResponse, tags=["Prediction"])
def predict_numeric(payload: ClaimInput):
    """Predict claim probability from policyholder + vehicle details."""
    try:
        return predict_claim_numeric(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Numeric prediction failed")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------
# IMAGE FRAUD PREDICTION
# ----------------------------------------------------------------
@app.post("/predict/image", tags=["Prediction"])
async def predict_image(file: UploadFile = File(...)):
    """Analyse a car damage image for fraud signals."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image files accepted.")
    try:
        return JSONResponse(content=predict_image_fraud(await file.read()))
    except Exception as e:
        logger.exception("Image prediction failed")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------
# COMBINED PREDICTION
# ----------------------------------------------------------------
@app.post("/predict/combined", response_model=CombinedPredictionResponse, tags=["Prediction"])
async def predict_combined(
    age_of_policyholder: float = Form(...),
    age_of_car: float = Form(...),
    fuel_type: str = Form(...),
    airbags: int = Form(...),
    policy_tenure: float = Form(0.5),
    ncap_rating: int = Form(0),
    file: UploadFile = File(None),
):
    """Combined: numeric form fields + optional image upload."""
    payload = ClaimInput(
        age_of_policyholder=age_of_policyholder,
        age_of_car=age_of_car,
        fuel_type=fuel_type,
        airbags=airbags,
        policy_tenure=policy_tenure,
        ncap_rating=ncap_rating,
    )
    try:
        numeric_result = predict_claim_numeric(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Numeric error: {e}")

    image_result = None
    if file and file.filename:
        try:
            image_result = predict_image_fraud(await file.read())
        except Exception as e:
            logger.warning(f"Image prediction skipped — {e}")

    # Merge scores
    claim_prob = numeric_result.claim_probability
    if image_result and image_result.get("confidence", 0) >= 0.6:
        weight = 0.3 if image_result["label"] == "Normal" else -0.2
        approval_score = round(max(0.0, min(1.0, (1 - claim_prob) * 0.7 + weight)), 4)
    else:
        approval_score = round(1 - claim_prob, 4)

    decision = (
        "Auto Approve" if approval_score > 0.70
        else "Manual Review" if approval_score > 0.40
        else "Investigate"
    )

    return CombinedPredictionResponse(
        numeric=numeric_result,
        image=image_result,
        final_approval_score=approval_score,
        final_decision=decision,
    )


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
