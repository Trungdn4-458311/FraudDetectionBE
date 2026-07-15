"""FastAPI — API chấm điểm gian lận real-time.

Chạy local:  uvicorn api:app --reload
Tài liệu tự sinh:  http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from scoring import score_txn, THRESHOLD, MODEL_NAME, FEATURES

app = FastAPI(
    title="Fraud Detection API",
    version="1.0",
    description="Chấm điểm gian lận cho giao dịch TRANSFER/CASH_OUT theo thời gian thực.",
)


class Transaction(BaseModel):
    type: str = Field(..., examples=["TRANSFER"], description="TRANSFER hoặc CASH_OUT")
    amount: float = Field(..., ge=0)
    oldbalanceOrg: float = Field(..., ge=0)
    newbalanceOrig: float = Field(..., ge=0)
    oldbalanceDest: float = Field(..., ge=0)
    newbalanceDest: float = Field(..., ge=0)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "type": "TRANSFER", "amount": 181.0,
                "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0,
                "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
            }]
        }
    }


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "threshold": THRESHOLD, "n_features": len(FEATURES)}


@app.post("/predict")
def predict(txn: Transaction):
    """Trả về xác suất gian lận + quyết định (APPROVE / BLOCK-REVIEW)."""
    return score_txn(txn.model_dump())
