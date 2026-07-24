# Kịch bản phát biểu — Module 5 (Modeling)

**Phạm vi:** slide **11 → 17** (chính) + 3 slide **Backup** (chỉ dùng khi bị hỏi).
**Thời lượng gợi ý:** ~6–7 phút cho 7 slide chính (~1 phút/slide, slide 16 dài hơn).

> Mạch xuyên suốt cần bám: **"Con số đẹp không phải do model giỏi, mà do dữ liệu dễ — và chúng tôi trung thực chỉ ra điều đó."** Đây là phần rubric cho điểm cao nhất.

---

## Slide 11 — *7. Results: 3 algorithms × 2 feature spaces* (~70s)

**Câu mở (nối từ người trước):**
> "Sau khi có feature, chúng tôi huấn luyện **3 thuật toán** — Logistic Regression, Random Forest, XGBoost — mỗi thuật toán trên **2 không gian đặc trưng Base và Full**, tổng cộng 6 mô hình. Bảng này là kết quả trên tập test."

**Chỉ vào 3 dòng, nhấn đúng 3 con số:**
- "**Random Forest Base** — dòng đậm — là mô hình **trung thực tốt nhất**: PR-AUC **0.9976**, và chỉ **1 báo động giả** trên **828.659** giao dịch hợp lệ, mà **không dùng một chút dữ liệu tổng hợp nào**."
- "Ngược lại, **Logistic Regression Base gần như vô dụng**: **49.287** báo động giả — tức khoảng **22 lần báo nhầm cho mỗi ca gian lận bắt được**. Vì sao? Vì một **siêu phẳng tuyến tính không diễn tả được tương tác giữa các cột số dư** — đây là manh mối đầu tiên cho thấy tín hiệu gian lận là **phi tuyến**."

**Chốt:** "Giữ ý này lại: mô hình tuyến tính thất bại, mô hình cây thì gần như hoàn hảo — lát nữa nó sẽ giải thích *vì sao* điểm cao đến vậy."

**Nếu bị hỏi "sao không nhìn accuracy?":** "Đoán "không bao giờ gian lận" đã đạt 99.87% accuracy → accuracy vô nghĩa ở đây, nên chúng tôi dùng PR-AUC / Recall / Precision."

---

## Slide 12 — *7. Precision–Recall curves* (~40s)

**Nói ngắn, để hình tự nói:**
> "Đây là đường Precision–Recall của cả 6 mô hình. **Đường tuyến tính** (baseline) tụt dần đều — precision rơi nhanh khi recall tăng. **Bốn đường cây** thì **ôm sát góc trên–phải**, tức giữ được precision cao gần như ở mọi mức recall."

**Vì sao dùng PR chứ không phải ROC:** "Với dữ liệu mất cân bằng 1:775, ROC-AUC trông đẹp giả tạo; PR-AUC phản ánh đúng cái giá của báo động giả."

**Chuyển slide:** "Câu hỏi tiếp theo: phần điểm số này có bao nhiêu là **thật**, bao nhiêu là do **rò rỉ nhãn** mà nhóm đã cảnh báo từ đầu?"

---

## Slide 13 — *8. Measuring the leakage we warned about* (~70s)

**Đây là slide "lấy điểm" — nói chậm, rõ:**
> "Từ đầu buổi nhóm đã thừa nhận: 9 đặc trưng tổng hợp được sinh ra **có điều kiện theo nhãn**, dùng ngây thơ là **rò rỉ nhãn**. Thay vì lờ đi, chúng tôi **đo** nó — bằng cách so PR-AUC của Full trừ Base cho từng thuật toán."

**Đọc cột Uplift:**
- "Với **Logistic Regression**, dữ liệu tổng hợp nâng điểm **+0.38** — rất lớn."
- "Nhưng với **Random Forest chỉ +0.0021**, **XGBoost chỉ +0.0052** — gần như bằng không."

**Ba gạch đầu dòng — đọc thành lời:**
> "Kết luận rút ra ba ý: **(1)** rò rỉ là **có thật** — nó cứu mô hình yếu; **(2)** nhưng nó **không phải trụ đỡ** — mô hình cây gần như chẳng được lợi gì; **(3)** mô hình trung thực tốt nhất của chúng tôi, RF Base, **không cần đến nó**."

**Chốt (câu quan trọng nhất slide):**
> "Nghĩa là **kết quả tiêu biểu của chúng tôi không dựa trên thông tin bị rò rỉ.**"

---

## Slide 14 — *8. Where the signal actually comes from* (~60s)

> "Nếu không phải dữ liệu tổng hợp, thì tín hiệu đến từ đâu? Biểu đồ độ quan trọng đặc trưng của XGBoost Full trả lời: **thanh xanh là feature PaySim thật, thanh cam là tổng hợp.**"

**Ba con số:**
- "**`errorBalanceOrig` một mình chiếm 53.7%** độ quan trọng — nó đo phần lệch số dư: tiền rời tài khoản gửi mà số dư không khớp."
- "Toàn bộ nhóm tổng hợp cộng lại chỉ **~28%**."
- "Và **các feature velocity gần như bằng 0.000** — tôi sẽ nói vì sao ở phần hạn chế."

**Chốt (chỉ vào thanh cao nhất):** "**Thanh cao nhất là một feature THẬT.** Model đang học từ chữ ký số học của PaySim, không phải từ nhãn rò rỉ."

---

## Slide 15 — *9. From probability to a business decision* (~70s)

> "Model xuất ra xác suất. Nhưng ngưỡng mặc định **0.5 không có ý nghĩa kinh doanh nào**. Chúng tôi quy đổi đánh đổi này thành **tiền**."

**Giải thích công thức bằng lời (đừng đọc ký hiệu):**
> "Chi phí tại ngưỡng t gồm hai phần: **phần một** là **tổng số tiền của các ca gian lận bị bỏ sót** — bỏ lọt một giao dịch lớn tốn hơn nhiều một giao dịch nhỏ, nên phạt theo đúng `amount`. **Phần hai** là **ma sát**: mỗi báo động giả tốn một chi phí cố định **C_FP = 10** — tương ứng công rà soát và một khách bị làm phiền."

**Chỉ vào đường cong + chốt:**
> "Quét toàn bộ ngưỡng, điểm chi phí thấp nhất là **t\* = 0.17, không phải 0.5** — và nó giảm **tổng chi phí 14.7%** so với ngưỡng mặc định."

---

## Slide 16 — *9. The business outcome* (~80s, slide dài nhất)

> "Áp ngưỡng tối ưu vào tập test, đây là kết quả **bằng ngôn ngữ kinh doanh**, không phải bằng metric ML:"

**Đọc bảng, nhấn 2 dòng xanh:**
- "Tổng giá trị gian lận **đang bị đe doạ**: ~3,62 tỷ."
- "Model **chặn được 3,61 tỷ — tức 99.96% giá trị gian lận.**"
- "Chỉ **lọt 1,36 triệu**, và tỉ lệ báo động giả chỉ **0.032% — 265 giao dịch**."

**So với hệ thống cũ (điểm nhấn thuyết phục):**
> "So với luật có sẵn của PaySim là `isFlaggedFraud` — nó chỉ bắt được **16** ca. Model của chúng tôi bắt **2.451 trên 2.459** ca gian lận."

**Câu về độ bền (quan trọng để phòng thủ giả định C_FP):**
> "Và đường chi phí **phẳng** ở vùng dưới t ≈ 0.25 — điểm tối ưu là một **vùng phẳng rộng**, nên kết quả **không nhạy** với giả định C_FP = 10 của chúng tôi."

---

## Slide 17 — *10. What our numbers really mean* (~70s) — **ĐỪNG BỎ SLIDE NÀY**

> "Slide cuối của phần tôi là phần quan trọng nhất về mặt học thuật. **PR-AUC 0.997 với 1 báo động giả KHÔNG phải để khoe.** Trong bài toán gian lận thực tế, con số này là **bất khả tín**. Lời giải thích nằm ở **dữ liệu, không phải model.**"

**Bốn ý — nói như kể chuyện:**
> "PaySim kịch bản hoá gian lận là **"rút sạch tài khoản"**, tạo ra một **dấu vết số học gần như xác định**. `errorBalanceOrig` bắt trực tiếp dấu vết đó — 53.7% độ quan trọng. Bằng chứng: mô hình **tuyến tính thất bại ở 0.59** trong khi cả hai mô hình **cây vượt 0.99** — chứng tỏ đây là **một luật phi tuyến, gần như xác định**. Còn feature tổng hợp thì chồng thêm rò rỉ lên trên."

**Chốt cả phần (câu kết mạnh):**
> "Nên chúng tôi khẳng định: **hiệu năng ngoài thực tế sẽ thấp hơn đáng kể.** Chúng tôi báo cáo điều này như một **hạn chế**, không phải một thành tích. Cảm ơn — mời [tên người tiếp theo] phần triển khai."

---

# Backup — thủ sẵn cho Q&A (không trình bày)

### Nếu bị hỏi: "Sao không dùng SMOTE / undersampling?" → Slide 23
- Đề bài cho chọn SMOTE **hoặc** undersampling **hoặc** class weights. Nhóm chọn **class weights** vì: (1) **không bịa thêm mẫu dương giả** trong một tập dữ liệu vốn đã có phần tổng hợp; (2) **giữ nguyên phân phối tập test**; (3) rẻ hơn nhiều trên 1,9 triệu dòng train.
- Áp cùng tỉ lệ **337:1** cho cả 3 thuật toán.

### Nếu bị hỏi: "Sao RF thắng XGBoost khi t=0.5?" → Slide 24
- Khoảng cách **xếp hạng nhỏ**: PR-AUC 0.9976 vs 0.9944.
- Khoảng cách **precision lớn**: 0.9996 vs 0.9222 (1 vs 206 FP).
- ⇒ Khác biệt là **hiệu chỉnh xác suất (calibration)**, không phải khả năng xếp hạng. XGBoost nhân gradient dương lên 337 lần → đẩy xác suất phình về phía dương, nhiều mẫu âm vượt 0.5 dù vẫn xếp *dưới* mẫu dương thật.
- **Chính vì thế chúng tôi tinh chỉnh ngưỡng thay vì tin vào 0.5.**

### Nếu bị hỏi về hạn chế → Slide 25
Sáu hạn chế: (1) dữ liệu mô phỏng đều đặn hơn thực tế; (2) feature tổng hợp suy ra từ nhãn; (3) velocity suy biến vì tài khoản hiếm lặp lại; (4) chia ngẫu nhiên chứ không theo thời gian; (5) C_FP=10 là giả định chứ chưa đo; (6) chỉ một lần chia, chưa báo cáo phương sai cross-validation.

---

## Bảng số liệu bỏ túi (để không đọc nhầm)

| Con số | Giá trị |
|---|---|
| RF Base PR-AUC / FP / FN | 0.9976 / **1** / 8 |
| XGB Base PR-AUC / FP | 0.9944 / 206 |
| LogReg Base PR-AUC / FP | 0.5932 / 49.287 |
| Uplift LogReg / RF / XGB | +0.3772 / +0.0021 / +0.0052 |
| `errorBalanceOrig` importance | 53.7% |
| Ngưỡng tối ưu t\* / giảm chi phí | 0.17 / −14.7% |
| Giá trị gian lận chặn được | 99.96% |
| FPR tại t\* | 0.032% (265 giao dịch) |
| Model bắt / Incumbent bắt | 2.451/2.459 vs **16** |
