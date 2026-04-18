# ================================================================
# AutoShield — Pydantic Schemas
# ================================================================

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


# ----------------------------------------------------------------
# INPUT
# ----------------------------------------------------------------
class ClaimInput(BaseModel):
    age_of_policyholder: float = Field(..., ge=18, le=100, description="Age of policyholder (years)")
    age_of_car: float = Field(..., ge=0, le=30, description="Age of car (years)")
    fuel_type: str = Field(..., description="Petrol | Diesel | CNG")
    airbags: int = Field(..., ge=0, le=12, description="Number of airbags")
    policy_tenure: float = Field(0.5, ge=0, le=1, description="Policy tenure (normalized 0–1)")
    ncap_rating: int = Field(0, ge=0, le=5, description="NCAP safety rating 0–5")

    class Config:
        json_schema_extra = {
            "example": {
                "age_of_policyholder": 35,
                "age_of_car": 3,
                "fuel_type": "Petrol",
                "airbags": 4,
                "policy_tenure": 0.6,
                "ncap_rating": 3,
            }
        }


# ----------------------------------------------------------------
# RESPONSES
# ----------------------------------------------------------------
class NumericPredictionResponse(BaseModel):
    claim_probability: float
    approval_probability: float
    risk_level: str
    approval_likelihood: str
    decision: str
    explanation: str


class HealthResponse(BaseModel):
    status: str
    numeric_model_loaded: bool
    image_model_loaded: bool


class CombinedPredictionResponse(BaseModel):
    numeric: NumericPredictionResponse
    image: Optional[Dict[str, Any]]
    final_approval_score: float
    final_decision: str
