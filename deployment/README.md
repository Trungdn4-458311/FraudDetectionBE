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

## Deploy lên Hugging Face Spaces (free)

1. Tạo Space mới: **New Space** → SDK **Streamlit** → chọn tên.
2. Upload toàn bộ file trong thư mục `deployment/` (gồm cả `model.joblib`) lên Space, hoặc `git push` vào repo của Space.
3. Space tự cài `requirements.txt` và chạy `app.py` → có **link công khai** (chính là deliverable "live link" của đề).

> Muốn kèm cả API FastAPI trên cùng Space: đổi sang SDK **Docker** và viết `Dockerfile` chạy đồng thời `uvicorn` + `streamlit`. Với yêu cầu đề bài, deploy Streamlit là đủ để có live link; API chạy/deploy riêng khi cần.
