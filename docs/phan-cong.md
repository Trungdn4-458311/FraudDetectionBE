# Phân công công việc — Đồ án Phát hiện gian lận thanh toán (PaySim)

Nhóm **4 thành viên**. Nguyên tắc: mỗi người *sở hữu* một mảng end-to-end (code + báo cáo + slide phần đó) để dễ quy trách nhiệm; phần lấy điểm cao nhất (modeling + khung rò rỉ nhãn) được ghép đôi.

> Rubric chấm **rigor và diễn giải trung thực** hơn là accuracy. Trọng tâm là khung **Base vs Full + rò rỉ nhãn**, và việc nêu thẳng các *limitation* (PaySim gần tách tuyến tính, velocity vô dụng, incumbent chỉ bắt 16 ca).

---

## Bảng phân công

| Người | Vai trò | Module | Việc cụ thể | Deliverable |
|---|---|---|---|---|
| **A** | Data & EDA | 1–2 | Nạp PaySim; sinh 9 feature tổng hợp (Faker); `data_dictionary`; toàn bộ biểu đồ EDA + phân tích tín hiệu tổng hợp | Notebook M1–2 chạy sạch; 5 hình xuất `report/figures/` |
| **B** | Cleaning & Feature Engineering | 3–4 | Làm sạch dữ liệu; `errorBalance*`; velocity features; lọc `TRANSFER`/`CASH_OUT`; dựng **Base vs Full**; feature selection (mutual information) | Notebook M3–4; bảng danh sách feature |
| **C** | Modeling *(lead)* | 5 | 6 mô hình (2× LogReg, RF, XGBoost); class weights; PR-AUC; **cost-based threshold (t\*=0.21)**; **khung phân tích rò rỉ nhãn** | Notebook M5; bảng kết quả so sánh |
| **D** | Deployment & Đóng gói | 6 + báo cáo/slide | FastAPI + Streamlit; export `model.joblib`; báo cáo LaTeX; biên tập slides | `deployment/`; `report/main.tex`; `slides/` |

---

## Vì sao chia như vậy

- **C là điểm neo học thuật.** Khung Base/Full + rò rỉ nhãn là phần lấy điểm cao nhất → giao cho người mạnh nhất nhóm. **B phải phối hợp chặt với C** vì Base/Full quyết định ngay từ tầng feature.
- **Trục phụ thuộc tuần tự.** `df` biến đổi qua từng module nên luồng là **A → B → C → D**. Thống nhất *interface* sớm: tên cột, thứ tự chạy cell, ai commit ô nào.
- **Cân tải.** D chạy song song được với modeling (deploy + báo cáo + slide) nên không bị nghẽn ở cuối.

---

## Việc chung (cả 4 người)

- Mỗi người viết **phần báo cáo + slide** ứng với module mình làm; **D tổng hợp** về một giọng văn thống nhất.
- Cùng rà **"honest limitations"** — đây là điểm cộng nếu nêu trung thực:
  - PaySim gần tách tuyến tính (RF Base PR-AUC 0.997, chỉ 1 false positive) → không phải model giỏi.
  - `errorBalanceOrig` chiếm ~53.7% importance → chữ ký balance gần như quyết định.
  - Velocity features suy biến trên PaySim (mean 1.00, importance 0.000).
  - Incumbent `isFlaggedFraud` chỉ bắt 16 ca.
- **Quy tắc commit:** không thêm AI co-author trailer (rubric yêu cầu code do nhóm tự viết); không commit file CSV 493 MB (đã `.gitignore`).

---

## Mốc thời gian gợi ý

| Tuần | Việc | Ai |
|---|---|---|
| 1 | Thống nhất interface module; A xong M1–2 | A (B/C/D review) |
| 2 | B xong M3–4 (Base/Full chốt) | B + C |
| 3 | C xong M5 (kết quả + threshold + framing) | C + B |
| 4 | D xong M6 + báo cáo + slides; cả nhóm rà limitation | D (cả nhóm) |

> Điền tên thật vào cột **Người** (A/B/C/D) trước khi nộp.
