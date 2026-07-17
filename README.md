# FraudDetectionBE — Real-Time Payment Fraud Detection

Đồ án Business Analytics: phát hiện gian lận giao dịch thanh toán end-to-end trên dữ liệu **PaySim**, kết hợp đặc trưng ngữ cảnh sinh bằng Faker. Toàn bộ phân tích nằm trong [`fraud_eda.ipynb`](fraud_eda.ipynb) (Module 1–6: Business Understanding → EDA → Cleaning → Feature Engineering → Modeling → Deployment).

## Dữ liệu (bắt buộc tải trước khi chạy)

File dataset gốc **không có trong repo** vì dung lượng ~493MB (vượt giới hạn 100MB của GitHub). Hãy tải và đặt vào **thư mục gốc** của dự án:

1. Tải "Online Payments Fraud Detection Dataset" từ Kaggle:
   https://www.kaggle.com/datasets/rupakroy/online-payments-fraud-detection-dataset
2. Đặt file `PS_20174392719_1491204439457_log.csv` ngay tại thư mục gốc (cùng cấp với `fraud_eda.ipynb`).

Notebook sẽ tự sinh 9 đặc trưng tổng hợp và xuất `data_dictionary.*`.

## Chạy notebook

Mở `fraud_eda.ipynb` (Jupyter/VSCode) và **Restart & Run All** — dữ liệu được xử lý tuần tự nên phải chạy từ đầu. Cần các thư viện: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `xgboost`, `faker`, `joblib`.

## Triển khai (Module 6)

Thư mục [`deployment/`](deployment/) chứa API real-time (FastAPI) + demo hàng đợi review (Streamlit). Chạy hết cell Module 6 trong notebook để sinh `deployment/model.joblib`, rồi:

```bash
cd deployment
pip install -r requirements.txt
uvicorn api:app --reload      # API + tài liệu tại /docs
streamlit run app.py          # UI review queue
```

Xem [`deployment/README.md`](deployment/README.md) để deploy lên Hugging Face Spaces.
