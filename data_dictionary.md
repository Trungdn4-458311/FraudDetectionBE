# Data Dictionary — Synthetic Features

| column                    | dtype        | unit        | valid_range           | generation_logic                                                                                                         |
|:--------------------------|:-------------|:------------|:----------------------|:-------------------------------------------------------------------------------------------------------------------------|
| account_age_days          | int32        | ngày        | 1–3650                | Tuổi tài khoản cấp theo nameOrig, phân phối Gamma; tài khoản từng gian lận trẻ hơn (mean ~44) so với hợp lệ (mean ~500). |
| home_country              | category/str | -           | ~240 quốc gia (Faker) | Quốc gia thanh toán của tài khoản, chọn ngẫu nhiên đều từ pool quốc gia sinh bởi Faker.                                  |
| device_fingerprint        | str (SHA1)   | -           | hash 40 ký tự hex     | Vân tay thiết bị thường dùng của tài khoản, sample từ pool 5.000 hash SHA1 (Faker).                                      |
| hour_of_day               | int16        | giờ         | 0–23                  | Suy trực tiếp từ step gốc: step % 24 (1 step = 1 giờ).                                                                   |
| shipping_billing_mismatch | int8 (0/1)   | cờ nhị phân | {0, 1}                | Lệch địa chỉ giao hàng vs thanh toán; Bernoulli p=0.40 nếu gian lận, p=0.03 nếu hợp lệ.                                  |
| is_new_device             | int8 (0/1)   | cờ nhị phân | {0, 1}                | Giao dịch từ thiết bị lạ; Bernoulli p=0.55 nếu gian lận, p=0.08 nếu hợp lệ.                                              |
| failed_payment_attempts   | int16        | lần         | >= 0 (thực tế 0–~10)  | Số lần thanh toán thất bại trước khi thành công; Poisson(λ=2.2) nếu gian lận, Poisson(λ=0.12) nếu hợp lệ.                |
| ip_billing_mismatch       | int8 (0/1)   | cờ nhị phân | {0, 1}                | IP khác quốc gia thanh toán; Bernoulli p=0.50 nếu gian lận, p=0.02 nếu hợp lệ.                                           |
| ip_billing_distance_km    | float64      | km          | 0–8000                | Khoảng cách IP tới nước thanh toán; Uniform(500, 8000) nếu ip_billing_mismatch=1, ngược lại Uniform(0, 80).              |