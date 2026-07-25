---
title: Fraud Detection Review Queue
emoji: 🛡️
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: 1.37.1
app_file: app.py
pinned: false
---

# Module 6 — Real-Time Payment Fraud Detection (Deployment)

Triển khai mô hình phát hiện gian lận thành **API real-time (FastAPI)** + **UI hàng đợi review (Streamlit)**.

## Nội dung thư mục

| File | Vai trò |
|------|---------|
| `model.joblib` | Model đã huấn luyện (**sinh từ notebook**, xem bên dưới) |
| `scoring.py` | Lõi chấm điểm dùng chung (featurize + score) |
| `api.py` | FastAPI — endpoint `/predict`, `/health` |
| `app.py` | Streamlit — hàng đợi review của chuyên viên |
| `sample_transactions.csv` | Dữ liệu mẫu cho demo |
| `requirements.txt` | Thư viện cần cài |

Mô hình deploy: **XGBoost Base** (chỉ đặc trưng giao dịch PaySim, không rò rỉ nhãn). Feature phía server tự suy: `errorBalanceOrig`, `errorBalanceDest`, `type_TRANSFER`. Ngưỡng chặn chọn theo tối ưu chi phí (Module 5.4).

## Bước 0 — Sinh `model.joblib` (bắt buộc trước khi chạy)

Trong `fraud_eda.ipynb`, chạy tới hết **Module 6** (cell export). Nó tạo `deployment/model.joblib`.

## Chạy local

```bash
pip install -r requirements.txt

# API real-time
uvicorn api:app --reload         # http://127.0.0.1:8000/docs

# UI review queue
streamlit run app.py             # http://localhost:8501
```

Ví dụ gọi API:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"type":"TRANSFER","amount":181,"oldbalanceOrg":181,"newbalanceOrig":0,"oldbalanceDest":0,"newbalanceDest":0}'
```

## Deploy (live link)

Đường deploy free-tier chính hiện nay là **Streamlit Community Cloud** — xem hướng dẫn đầy đủ trong [`DEPLOY.md`](DEPLOY.md) (Route 0). Tóm tắt:

1. Push repo lên GitHub, vào [share.streamlit.io](https://share.streamlit.io) → **New app**.
2. Chọn repo, đặt `deployment/app.py` làm entry point (đã có sẵn `requirements.txt` và `model.joblib`).
3. Streamlit tự build và cấp **link công khai** — chính là deliverable "live link" của đề.

> **Lưu ý:** Hugging Face Spaces free tier hiện không còn chạy app Streamlit/Docker liên tục (cần HF **PRO**). YAML header phía trên file này vẫn dùng được nếu deploy lên HF PRO. Ngoài ra repo đã có **demo chạy client-side** trên GitHub Pages (thư mục [`web/`](../web/)) làm live link không cần server Python.
