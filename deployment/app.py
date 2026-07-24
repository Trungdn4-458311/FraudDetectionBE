"""Streamlit — Hàng đợi review giao dịch nghi gian lận (mô phỏng chuyên viên chống gian lận).

Chạy local:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from scoring import score_txn, THRESHOLD, BLOCK_THRESHOLD, MODEL_NAME, RAW_FIELDS

HERE = Path(__file__).resolve().parent

st.set_page_config(page_title="Fraud Review Queue", page_icon="🛡️", layout="wide")
st.title("🛡️ Hàng đợi review giao dịch nghi gian lận")
st.caption(f"Mô hình deploy: **{MODEL_NAME}** · Chính sách rủi ro 3 mức — "
           f"duyệt < **{THRESHOLD:.2f}** ≤ review < **{BLOCK_THRESHOLD:.2f}** ≤ chặn tự động")


def score_frame(df: pd.DataFrame) -> pd.DataFrame:
    res = [score_txn(r) for r in df.to_dict("records")]
    out = df.copy()
    out["fraud_probability"] = [r["fraud_probability"] for r in res]
    out["decision"] = [r["decision"] for r in res]
    out["risk_tier"] = [r["risk_tier"] for r in res]
    return out.sort_values("fraud_probability", ascending=False).reset_index(drop=True)


mode = st.sidebar.radio("Nguồn dữ liệu", ["Mẫu có sẵn", "Tải CSV lên", "Nhập tay 1 giao dịch"])

# ---- Chế độ nhập tay 1 giao dịch ----
if mode == "Nhập tay 1 giao dịch":
    st.subheader("Chấm điểm 1 giao dịch")
    c1, c2, c3 = st.columns(3)
    typ = c1.selectbox("type", ["TRANSFER", "CASH_OUT"])
    amount = c1.number_input("amount", min_value=0.0, value=181.0)
    old_org = c2.number_input("oldbalanceOrg", min_value=0.0, value=181.0)
    new_orig = c2.number_input("newbalanceOrig", min_value=0.0, value=0.0)
    old_dest = c3.number_input("oldbalanceDest", min_value=0.0, value=0.0)
    new_dest = c3.number_input("newbalanceDest", min_value=0.0, value=0.0)
    if st.button("Chấm điểm", type="primary"):
        r = score_txn({"type": typ, "amount": amount, "oldbalanceOrg": old_org,
                       "newbalanceOrig": new_orig, "oldbalanceDest": old_dest,
                       "newbalanceDest": new_dest})
        show = {"BLOCK": st.error, "REVIEW": st.warning, "APPROVE": st.success}[r["decision"]]
        show(f"{r['decision']} ({r['risk_tier']}) — xác suất gian lận = {r['fraud_probability']:.2%}")
        st.json(r)
    st.stop()

# ---- Chế độ hàng đợi ----
if mode == "Mẫu có sẵn":
    df = pd.read_csv(HERE / "sample_transactions.csv")
else:
    up = st.sidebar.file_uploader("CSV giao dịch", type="csv")
    if up is None:
        st.info("Tải lên CSV có các cột: " + ", ".join(RAW_FIELDS))
        st.stop()
    df = pd.read_csv(up)

missing = [c for c in RAW_FIELDS if c not in df.columns]
if missing:
    st.error(f"CSV thiếu cột bắt buộc: {missing}")
    st.stop()

if len(df) == 0:
    st.info("CSV không có dòng dữ liệu để chấm điểm.")
    st.stop()

scored = score_frame(df)
n_block = int((scored["decision"] == "BLOCK").sum())
n_review = int((scored["decision"] == "REVIEW").sum())
n_approve = int((scored["decision"] == "APPROVE").sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng giao dịch", len(scored))
m2.metric("⛔ Chặn tự động", n_block)
m3.metric("🔍 Cần review", n_review)
m4.metric("✅ Duyệt tự động", n_approve)

st.subheader("Hàng đợi — rủi ro cao ➜ thấp")
st.dataframe(
    scored.style.background_gradient(subset=["fraud_probability"], cmap="Reds"),
    use_container_width=True,
)

st.subheader("Xử lý giao dịch")
idx = int(st.number_input("Chọn dòng để xử lý", min_value=0,
                          max_value=max(len(scored) - 1, 0), value=0))
st.write(scored.iloc[idx].to_dict())

if "actions" not in st.session_state:
    st.session_state["actions"] = {}
c1, c2 = st.columns(2)
if c1.button("✅ Duyệt (Approve)"):
    st.session_state["actions"][idx] = "APPROVED"
if c2.button("⛔ Chặn (Block)"):
    st.session_state["actions"][idx] = "BLOCKED"
if st.session_state["actions"]:
    st.write("Nhật ký xử lý của chuyên viên:", st.session_state["actions"])
