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
THRESHOLD = float(_bundle["threshold"])            # ranh giới review (tối ưu chi phí, mục 5.4)
# Ngưỡng auto-block: điểm đủ cao để chặn tự động (còn lại -> hàng đợi review thủ công).
# Ưu tiên giá trị hiệu chỉnh trong bundle (precision >= 0.99 trên test), fallback 0.80,
# ghi đè được bằng biến môi trường BLOCK_THRESHOLD.
BLOCK_THRESHOLD = float(os.environ.get(
    "BLOCK_THRESHOLD", _bundle.get("block_threshold", 0.80)))
# Invariant: auto-block boundary must sit at/above the review boundary, else the
# manual-review band is empty (a misconfigured env override could invert them).
BLOCK_THRESHOLD = max(BLOCK_THRESHOLD, THRESHOLD)
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


def decide(prob: float) -> tuple[str, str]:
    """Chính sách rủi ro 3 mức (risk-policy) — ánh xạ điểm số sang hành động:

        prob >= BLOCK_THRESHOLD   -> BLOCK   (auto-block: chặn tự động, độ tin cậy cao)
        THRESHOLD <= prob         -> REVIEW  (manual-review: đẩy vào hàng đợi chuyên viên)
        prob <  THRESHOLD         -> APPROVE (auto-approve: duyệt tự động)

    Tách auto-block khỏi manual-review giúp cân bằng chặn gian lận vs ma sát khách hàng:
    chỉ chặn tự động khi mô hình gần như chắc chắn; vùng xám dành cho người review.
    """
    if prob >= BLOCK_THRESHOLD:
        return "BLOCK", "auto-block"
    if prob >= THRESHOLD:
        return "REVIEW", "manual-review"
    return "APPROVE", "auto-approve"


def score_txn(txn: dict) -> dict:
    """Trả về xác suất gian lận + quyết định theo chính sách rủi ro 3 mức."""
    X = featurize(txn)
    prob = float(MODEL.predict_proba(X)[0, 1])
    decision, tier = decide(prob)
    return {
        "fraud_probability": round(prob, 6),
        "flagged_fraud": bool(prob >= THRESHOLD),   # REVIEW hoặc BLOCK đều là "gắn cờ"
        "decision": decision,                        # APPROVE | REVIEW | BLOCK
        "risk_tier": tier,                           # auto-approve | manual-review | auto-block
        "threshold": THRESHOLD,
        "block_threshold": BLOCK_THRESHOLD,
        "model": MODEL_NAME,
    }
