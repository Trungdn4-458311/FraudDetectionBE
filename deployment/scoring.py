"""Chấm điểm gian lận cho 1 giao dịch — dùng chung bởi API (FastAPI) và UI (Streamlit).

Model được sinh từ notebook (cell Module 6 -> deployment/model.joblib).
Có thể trỏ tới file model khác qua biến môi trường MODEL_PATH (dùng khi test).
"""
import os
from pathlib import Path

import joblib
import pandas as pd

MODEL_PATH = os.environ.get("MODEL_PATH", str(Path(__file__).with_name("model.joblib")))

_bundle = joblib.load(MODEL_PATH)
MODEL = _bundle["model"]
FEATURES = list(_bundle["features"])
THRESHOLD = float(_bundle["threshold"])
MODEL_NAME = _bundle.get("model_name", "model")

# Các trường thô mà người gọi phải cung cấp cho 1 giao dịch
RAW_FIELDS = ["type", "amount", "oldbalanceOrg", "newbalanceOrig",
              "oldbalanceDest", "newbalanceDest"]


def featurize(txn: dict) -> pd.DataFrame:
    """Từ field thô của 1 giao dịch -> DataFrame đúng thứ tự đặc trưng của model."""
    amount = float(txn["amount"])
    old_org = float(txn["oldbalanceOrg"])
    new_orig = float(txn["newbalanceOrig"])
    old_dest = float(txn["oldbalanceDest"])
    new_dest = float(txn["newbalanceDest"])
    row = {
        "amount": amount,
        "oldbalanceOrg": old_org,
        "newbalanceOrig": new_orig,
        "oldbalanceDest": old_dest,
        "newbalanceDest": new_dest,
        # đặc trưng suy diễn (server tự tính, khớp Module 2.5)
        "errorBalanceOrig": new_orig + amount - old_org,
        "errorBalanceDest": old_dest + amount - new_dest,
        "type_TRANSFER": 1 if str(txn.get("type", "")).upper() == "TRANSFER" else 0,
    }
    return pd.DataFrame([row])[FEATURES]


def score_txn(txn: dict) -> dict:
    """Trả về xác suất gian lận + quyết định theo ngưỡng đã chọn."""
    X = featurize(txn)
    prob = float(MODEL.predict_proba(X)[0, 1])
    flagged = bool(prob >= THRESHOLD)
    return {
        "fraud_probability": round(prob, 6),
        "flagged_fraud": flagged,
        "decision": "BLOCK / REVIEW" if flagged else "APPROVE",
        "threshold": THRESHOLD,
        "model": MODEL_NAME,
    }
