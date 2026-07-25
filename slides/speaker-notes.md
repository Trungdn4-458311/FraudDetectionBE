# Kịch bản phát biểu — Fraud Detection (Module 1–8)

**Tổng thời lượng:** ~18–20 phút (19 slide chính + 3 slide dự phòng)
**File slide:** `slides/main.pdf`

> **Mạch kể xuyên suốt:** Chúng tôi làm đúng quy trình → phát hiện một cái bẫy trong chính dữ liệu của mình → thiết kế thí nghiệm để đo cái bẫy đó → và cuối cùng tự phản biện kết quả đẹp của mình.
>
> Đây là điểm khiến bài của nhóm khác biệt. **Đừng khoe điểm 0.997 — hãy khoe việc mình hiểu tại sao nó cao.**

---

## Slide 1 — Title *(20 giây)*

> "Chào thầy/cô và các bạn. Nhóm em trình bày đồ án phát hiện gian lận thanh toán thời gian thực cho nền tảng thương mại điện tử, phạm vi từ Module 1 đến Module 8."

Ngắn gọn, không đọc lại tên slide.

---

## Slide 2 — Agenda *(40 giây)*

> "Bài trình bày gồm 10 phần theo đúng 5 module. Nhưng nếu chỉ nhớ một điều, em mong mọi người nhớ dòng này: **mô hình tốt nhất của nhóm đạt PR-AUC 0.997 — và phần thú vị nhất là tại sao con số đó không ấn tượng như vẻ ngoài của nó.**"

**Nhấn:** Câu này gieo tò mò cho cả bài. Dừng 1 nhịp sau khi nói.

---

## Slide 3 — Bài toán nghiệp vụ *(1,5 phút)*

> "Câu hỏi nghiệp vụ là: giao dịch nào có khả năng gian lận, và cân bằng thế nào giữa chặn gian lận với việc không gây phiền cho khách hàng hợp lệ.
>
> Gian lận chỉ chiếm 0,129% giao dịch — rất hiếm. Nhưng giá trị trung bình lớn gấp 8,2 lần giao dịch thường, tổng rủi ro khoảng 12,1 tỷ.
>
> Điều quan trọng là: **chặn cũng tốn kém**. Mỗi lần chặn nhầm là một khách hàng thật bị từ chối — sinh ma sát, bỏ giỏ hàng, rời bỏ nền tảng.
>
> Nên mục tiêu không phải 'bắt được càng nhiều càng tốt', mà là **tìm điểm vận hành tối thiểu hoá tổng chi phí kinh doanh**."

**Nhấn:** Câu cuối — đây là lý do sau này có phần chọn ngưỡng theo chi phí.

---

## Slide 4 — KPI *(1 phút)*

> "Nhóm theo dõi 3 KPI: fraud rate đo quy mô rủi ro, false-positive rate đo ma sát khách hàng, và financial loss avoided đo giá trị kinh doanh.
>
> Và đây là lý do **không dùng Accuracy**: một mô hình dự đoán 'không bao giờ gian lận' đạt 99,87% accuracy nhưng bắt được **đúng 0 vụ**. Với dữ liệu mất cân bằng, accuracy vô nghĩa. Nhóm dùng PR-AUC, Recall và F1."

**Nhấn:** Ví dụ 99,87% rất dễ nhớ — nói chậm chỗ này.

---

## Slide 5 — Hai nguồn dữ liệu *(1,5 phút)*

> "Đề bài yêu cầu kết hợp 2 nguồn. Nguồn 1 là PaySim từ Kaggle: 6,36 triệu giao dịch mô phỏng trong 31 ngày, có số dư trước/sau và nhãn gian lận thật.
>
> Nguồn 2 nhóm tự sinh bằng thư viện Faker: 9 đặc trưng ngữ cảnh như tuổi tài khoản, thiết bị lạ, lệch địa chỉ giao–thanh toán, khoảng cách IP. Tất cả được ghi tài liệu đầy đủ trong data dictionary.
>
> Điểm cần lưu ý: nhóm sinh chúng **có điều kiện theo nhãn** — ví dụ xác suất dùng thiết bị lạ là 55% nếu gian lận, 8% nếu hợp lệ. Đây là chủ ý, để tín hiệu trông thực tế."

**Chuyển tiếp:** "Và chính chỗ này dẫn tới vấn đề lớn nhất của đồ án."

---

## Slide 6 — ⚠️ Cái bẫy *(2 phút — SLIDE QUAN TRỌNG)*

> "Khi kiểm chứng, các đặc trưng tổng hợp tách hai lớp cực kỳ đẹp: tài khoản gian lận trẻ hơn 11 lần, tỉ lệ lệch IP cao gấp 25 lần.
>
> Nhìn qua thì tuyệt vời. Nhưng hãy nhớ: **chính nhóm em đã sinh ra chúng từ nhãn.** Nghĩa là sức mạnh dự báo đó là *do thiết kế*, không phải *phát hiện được từ dữ liệu*.
>
> Nếu nhét thẳng vào mô hình, đó là **rò rỉ nhãn** — chúng em sẽ tự chấm bài của chính mình.
>
> Nhóm có 2 lựa chọn: giả vờ không thấy, hoặc xử lý nó minh bạch. Nhóm chọn cách thứ hai: **xây hai không gian đặc trưng và so sánh ở mọi bước.**"

**Nhấn:** Đây là slide "ăn điểm" nhất. Nói chậm, nhìn xuống khán giả. Cụm "tự chấm bài của chính mình" rất dễ nhớ.

---

## Slide 7 — Thiết kế Base / Full *(1,5 phút)*

> "**Base** gồm 11 đặc trưng, chỉ từ dữ liệu PaySim thật — số tiền, số dư, lỗi số dư, velocity. Không rò rỉ, phản ánh đúng độ khó thực tế.
>
> **Full** là Base cộng 7 tín hiệu tổng hợp. Có rò rỉ, nên là cận trên lạc quan.
>
> Mỗi thuật toán được huấn luyện trên **cả hai**. Nhờ vậy khoảng cách giữa chúng không còn là thứ phải che giấu — nó **trở thành phép đo** mức độ rò rỉ."

**Nhấn:** "biến khuyết điểm thành phép đo" — đây là đóng góp phương pháp của nhóm.

---

## Slide 8 — EDA *(2 phút)*

> "Hai phát hiện định hình toàn bộ phần sau.
>
> **Thứ nhất**, gian lận chỉ xảy ra ở 2 trong 5 loại giao dịch: TRANSFER và CASH_OUT. Ba loại còn lại đúng bằng 0. Nên nhóm lọc trước theo loại — mật độ nhãn dương tăng từ 0,129% lên 0,296%, **hơn gấp đôi mà không mất chút thông tin nào**.
>
> **Thứ hai**, gian lận trong PaySim là kịch bản 'rút sạch tài khoản'. Nhóm tạo đặc trưng *lỗi số dư*: số dư sau cộng số tiền trừ số dư trước — nếu giao dịch hợp lệ thì bằng 0.
>
> So sánh: quy tắc ngây thơ 'tài khoản bị rút sạch' chỉ cho tỉ lệ gian lận 0,223%, tức 1,7 lần. Nhưng công thức *lỗi số dư* sắc hơn nhiều — và sau này nó thành đặc trưng số một."

---

## Slide 9 — Làm sạch dữ liệu *(1,5 phút)*

> "Dữ liệu rất sạch: không thiếu, không trùng, chỉ 16 dòng vi phạm ràng buộc.
>
> Nhưng có một quyết định nhóm tâm đắc. Quy tắc IQR chuẩn gắn cờ 338 nghìn giao dịch là outlier — 5,3% dữ liệu. Sách giáo khoa bảo: loại bỏ.
>
> **Nhóm giữ lại toàn bộ.** Lý do bằng số liệu: tỉ lệ gian lận *bên trong* nhóm outlier là 1,14%, gấp **8,8 lần** toàn cục. Cắt đuôi là xoá đi chính những nhãn dương hiếm hoi.
>
> Trong bài toán gian lận, số tiền lớn là **tín hiệu**, không phải nhiễu."

**Nhấn:** Đây là chỗ chứng minh nhóm hiểu bài chứ không áp dụng máy móc. Nếu bị hỏi "sao không loại outlier?" thì slide này đã trả lời sẵn.

---

## Slide 10 — Feature engineering *(1,5 phút)*

> "Về mất cân bằng 1:337, nhóm dùng **trọng số lớp** ở cả 3 mô hình, và điều quan trọng là cả ba đều áp cùng tỉ lệ phạt 337:1 — nên so sánh giữa chúng là công bằng.
>
> Về feature selection, nhóm gặp một tình huống thú vị: mutual information xếp `errorBalanceOrig` chỉ hạng 5, nhưng nó lại là đặc trưng số 1 trong mô hình. Lý do là MI chỉ xét **đơn biến**, không thấy được tương tác. Nếu cắt máy móc theo MI, nhóm đã xoá mất đặc trưng tốt nhất. Nên nhóm giữ toàn bộ.
>
> Cuối cùng là một kết quả âm tính nhóm xin báo cáo trung thực: hai đặc trưng velocity mà đề bài yêu cầu **gần như vô dụng trên PaySim**, vì tài khoản hầu như không lặp lại. Nhóm vẫn xây đúng, nhưng importance bằng 0."

**Nhấn:** Việc chủ động báo cáo kết quả âm tính tạo ấn tượng rất tốt về tính trung thực.

---

## Slide 11 — Bảng kết quả *(2 phút)*

> "Đây là 6 mô hình: 3 thuật toán nhân 2 bộ đặc trưng.
>
> Nổi bật nhất: **Random Forest trên bộ Base** — PR-AUC 0,997, và chỉ **1 cảnh báo giả** trên 828 nghìn giao dịch hợp lệ. Quan trọng là nó **không dùng chút dữ liệu tổng hợp nào**.
>
> Ngược lại, Logistic Regression Base không dùng được: nó chặn 49 nghìn khách hàng thật để bắt 2.233 vụ — tức 22 báo động giả cho mỗi vụ bắt được. Lý do là mô hình tuyến tính không biểu diễn nổi tương tác lỗi số dư."

**Mẹo:** Chỉ tay vào cột FP. Con số "1" và "49.287" cạnh nhau rất ấn tượng.

---

## Slide 12 — PR curves *(45 giây)*

> "Biểu đồ này cho thấy rõ hơn bảng số: đường xanh của mô hình tuyến tính tụt dần, còn bốn đường của mô hình cây bám sát góc trên bên phải — gần như trùng nhau. Chính vì trùng nhau nên PR-AUC không tách được chúng, phải nhìn vào ma trận nhầm lẫn."

---

## Slide 13 — Đo mức rò rỉ *(1,5 phút — SLIDE QUAN TRỌNG)*

> "Bây giờ quay lại cái bẫy ở đầu bài. Nhờ thiết kế Base/Full, nhóm **đo được** nó.
>
> Với mô hình tuyến tính, thêm dữ liệu tổng hợp làm PR-AUC nhảy **+0,377**. Rất lớn.
>
> Nhưng với hai mô hình cây, mức tăng chỉ **+0,002 và +0,005** — gần như không có.
>
> Kết luận: rò rỉ là **có thật**, nhưng nó **không gánh** mô hình tốt. Mô hình trung thực nhất của nhóm không cần đến nó chút nào. Nghĩa là kết luận chính của nhóm **không dựa trên thông tin bị rò rỉ**."

**Nhấn:** Đây là chỗ "đóng" lời hứa đã gieo ở slide 6. Nói dứt khoát.

---

## Slide 14 — Feature importance *(1 phút)*

> "Biểu đồ này xác nhận bằng mắt: màu xanh là đặc trưng thật, màu cam là tổng hợp.
>
> Cột dài nhất — `errorBalanceOrig` — chiếm 53,7%, và nó là **đặc trưng thật**. Các cột cam đều ngắn. Còn hai đặc trưng velocity ở dưới cùng đúng bằng 0, khớp với điều nhóm vừa nói."

---

## Slide 15 — Chọn ngưỡng theo chi phí *(1,5 phút)*

> "Ngưỡng mặc định 0,5 chỉ là quy ước thống kê, không mang ý nghĩa kinh doanh. Nhóm quy đổi đánh đổi ra **tiền**: mỗi vụ bỏ sót mất đúng số tiền giao dịch; mỗi báo động giả tốn một khoản ma sát cố định.
>
> Quét toàn bộ ngưỡng, chi phí thấp nhất rơi vào **0,17**, không phải 0,5 — giảm tổng chi phí **14,7%**.
>
> Và nhìn hình sẽ thấy đường chi phí **phẳng** ở vùng dưới 0,25 rồi mới dốc lên. Nghĩa là điểm tối ưu là một **cao nguyên**, nên kết quả khá vững trước giả định về chi phí ma sát."

---

## Slide 16 — Kết quả nghiệp vụ *(1 phút)*

> "Tại ngưỡng 0,17: mô hình chặn được **99,96% giá trị gian lận**, chỉ để lọt 1,36 triệu, với tỉ lệ chặn nhầm chỉ **0,032%** — tức 265 giao dịch.
>
> Để so sánh: hệ thống luật sẵn có trong PaySim chỉ bắt được **16 vụ**, còn mô hình của nhóm bắt **2.451 trên 2.459**."

**Nhấn:** So sánh 16 vs 2.451 rất mạnh — đây là "giá trị gia tăng" của cả đồ án.

---

## Slide 17 — ⚠️ Ý nghĩa thật của con số *(1,5 phút — SLIDE QUAN TRỌNG)*

> "Đến đây nhóm muốn tự phản biện. PR-AUC 0,997 với 1 báo động giả — trong thực tế con số này là **không tưởng**. Nên nhóm phải giải thích, chứ không ăn mừng.
>
> Nguyên nhân nằm ở **dữ liệu, không phải mô hình**. PaySim mô phỏng gian lận bằng kịch bản 'rút sạch tài khoản', để lại dấu vết số học **gần như tất định**, và `errorBalanceOrig` bắt trúng ngay dấu vết đó.
>
> Bằng chứng: mô hình **tuyến tính thất bại** với 0,59, trong khi hai mô hình cây đều vượt 0,99. Chênh lệch đó cho thấy toàn bộ hiệu năng đến từ **một quy luật phi tuyến gần như tất định**.
>
> Vì vậy nhóm báo cáo đây là **hạn chế**, không phải thành tích. Trên dữ liệu thật, hiệu năng chắc chắn thấp hơn nhiều."

**Nhấn:** Slide này thể hiện độ chín về tư duy. Đừng vội, nói chậm và tự tin.

---

## Triển khai — API + hàng đợi review (Module 6) *(1 phút)*

> "Sang phần triển khai — Module 6. Mô hình không dừng ở notebook: nhóm đóng gói thành **API thời gian thực** (FastAPI, endpoint `/predict`) và một **giao diện hàng đợi review** cho nhân viên (Streamlit). Mỗi giao dịch vào nhận một quyết định **3 mức** kèm nhật ký hành động.
>
> Và để thầy/cô kiểm chứng trực tiếp, nhóm có bản **demo chạy thẳng trên trình duyệt** — toàn bộ mô hình 300 cây chạy phía client, không cần server, và khớp với API Python tới 2×10⁻⁷."

**Nhấn:** Đây chính là "live link" đề yêu cầu — mở được ngay, không cần cài đặt.

---

## Giám sát — trôi dữ liệu & huấn luyện lại (Module 7) *(1 phút)*

> "Module 7 — giám sát. Mô hình sẽ xuống cấp khi dữ liệu thật đổi theo thời gian, nên nhóm **tự viết** một thư viện giám sát (không dùng thư viện ngoài, để đảm bảo tính nguyên bản) rồi kết xuất ra dashboard HTML.
>
> Điểm nhóm muốn nhấn: nhóm gắn cảnh báo trôi dữ liệu vào **độ lớn hiệu ứng** (PSI, thống kê KS), **không** vào p-value. Vì ở quy mô hơn 400 nghìn giao dịch mỗi cửa sổ, p-value luôn xấp xỉ 0 và sẽ báo động giả toàn bộ — trên dữ liệu thật, cả 8/8 đặc trưng có p-value ≈ 0 nhưng **không** đặc trưng nào lệch thực sự.
>
> Nhóm còn thêm một bài **kiểm thử chịu tải** bơm nhiễu vào để chứng minh cơ chế cảnh báo **thật sự kích hoạt**, chứ không chỉ luôn báo 'ổn'."

**Nhấn:** "Đo độ lớn hiệu ứng, không đo p-value" — đây là điểm phương pháp đáng ghi điểm nhất của module này.

---

## Chính sách rủi ro — từ điểm số đến hành động (Module 8) *(45 giây)*

> "Cuối cùng, Module 8 — biến một điểm số thành hành động nghiệp vụ. **Ba mức**: dưới ngưỡng vận hành thì duyệt tự động; vùng giữa đẩy sang nhân viên review; chỉ khi điểm rất cao mới chặn tự động.
>
> Ngưỡng vận hành của mô hình triển khai là **0,09** (chọn theo chi phí, khác 0,17 của mô hình phân tích). Ngưỡng chặn tự động **b ≈ 0,80**: nhóm **nhắm tới** precision ≥ 0,99, nhưng mô hình 8 đặc trưng không đạt mức đó nên nhóm **lùi về mức thận trọng 0,80** — chặn tự động chỉ dành cho trường hợp gần như chắc chắn.
>
> Tín hiệu đẩy một giao dịch lên cao vẫn là `errorBalanceOrig` — số dư gốc không khớp với số tiền chuyển."

---

## Slide 18 — Kết luận *(1 phút)*

> "Tóm lại, nhóm đã hoàn thành trọn vẹn Module 1 đến 8: hai nguồn dữ liệu với data dictionary đầy đủ, làm sạch có nhật ký kiểm chứng, 3 thuật toán trên 2 bộ đặc trưng, ngưỡng vận hành chọn theo chi phí, cùng với triển khai API + hàng đợi review, giám sát trôi dữ liệu, và chính sách rủi ro 3 mức.
>
> Khuyến nghị: **Random Forest Base** là mô hình trung thực tốt nhất; **XGBoost Base** để triển khai vì gọn và nhanh; vận hành tại ngưỡng 0,17 (mô hình phân tích) — mô hình triển khai dùng ngưỡng riêng ≈0,09.
>
> Nhưng điều nhóm tâm đắc nhất không phải điểm số, mà là: nhóm đã **biến một lỗ hổng rò rỉ nhãn tiềm ẩn thành một đại lượng đo được**, và giải thích được chính xác vì sao điểm của mình lại cao."

---

## Slide 19 — Cảm ơn *(15 giây)*

> "Phần trình bày của nhóm đến đây là hết. Nhóm xin lắng nghe câu hỏi ạ."

---

# Chuẩn bị hỏi đáp

| Câu hỏi có thể gặp | Trả lời ngắn |
|---|---|
| **"Sao điểm cao bất thường vậy?"** | Đã có sẵn slide 17. Nhấn: dữ liệu mô phỏng có dấu vết số dư gần như tất định; bằng chứng là mô hình tuyến tính vẫn thất bại. |
| **"Sao không dùng SMOTE?"** | → **Slide backup 1**. Đề cho phép chọn 1 trong 3; nhóm chọn class weights vì không muốn bịa thêm mẫu tổng hợp trong bộ dữ liệu vốn đã có phần tổng hợp, và rẻ hơn nhiều trên 1,9 triệu dòng. |
| **"Rò rỉ nhãn là gì? Sao không bỏ luôn feature đó?"** | Vì trong hệ thống thật, thiết bị lạ hay lệch IP **là tín hiệu hợp lệ, quan sát được lúc chấm điểm**. Vấn đề chỉ là *độ mạnh* của chúng ở đây do nhóm tự đặt. Nên nhóm giữ và **đo** thay vì bỏ. |
| **"Sao RF thắng XGBoost?"** | → **Slide backup 2**. Khoảng cách xếp hạng rất nhỏ (0,9974 vs 0,9944); chênh lệch lớn ở precision là do **calibration** — XGBoost nhân gradient dương lên 337 lần nên đẩy xác suất lên cao. Đó chính là lý do phải chỉnh ngưỡng. |
| **"COST_FP = 10 lấy ở đâu?"** | Là **giả định** nhóm nêu rõ, không phải đo được. Nhưng đường chi phí phẳng ở vùng tối ưu nên kết quả ít nhạy. Triển khai thật cần đo từ chi phí review và tỉ lệ khách rời bỏ. |
| **"Velocity vô dụng sao vẫn làm?"** | Đề bài yêu cầu, nhóm xây đúng và nhân quả (chỉ dùng quá khứ). Vô dụng là do **đặc thù PaySim** (tài khoản không lặp), không phải do cài sai. Trên nền tảng thật có khách quay lại thì rất giá trị. |
| **"Sao chỉ chia 70/30, không cross-validation?"** | Thừa nhận thẳng — đây là hạn chế đã ghi trong báo cáo (slide backup 3). Hướng cải tiến: chia theo **thời gian** và báo cáo phương sai qua nhiều lần chia. |

---

# Mẹo trình bày

1. **Ba slide phải nói tốt nhất:** 6 (cái bẫy), 13 (đo rò rỉ), 17 (ý nghĩa thật). Đây là mạch tư duy khiến bài nổi bật.
2. **Đừng đọc số trên slide** — khán giả tự đọc được. Hãy nói *ý nghĩa* của số đó.
3. **Cặp số dễ nhớ nên nhấn:** `1 vs 49.287` (false positive), `16 vs 2.451` (so với hệ thống cũ), `8,8 lần` (mật độ gian lận trong outlier).
4. **Nếu bị hỏi khó và không chắc:** nói thẳng "đây là hạn chế nhóm đã ghi nhận trong báo cáo" — trung thực ăn điểm hơn là đoán bừa.
5. **Nếu thiếu thời gian:** cắt slide 12 (PR curves) và 14 (importance) — nội dung đã có ở slide 11 và 13.
