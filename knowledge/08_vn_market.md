# 🇻🇳 08 — Thị trường chứng khoán Việt Nam

Đặc thù của thị trường VN ảnh hưởng trực tiếp đến cách xử lý data và mô hình hoá. Phần này giúp tránh giả định sai khi áp công thức Mỹ/Châu Âu vào data VN.

## 1. Sàn giao dịch

| Sàn       | Tên đầy đủ                  | Mã ticker (project)      |
| --------- | --------------------------- | ------------------------ |
| **HOSE**  | Ho Chi Minh Stock Exchange  | VCB, FPT, HPG, VIC, VNM (tất cả) |
| **HNX**   | Hanoi Stock Exchange        | —                        |
| **UPCoM** | Sàn cho công ty chưa niêm yết | —                       |

> Cả 5 mã trong project đều ở **HOSE** — hành vi giao dịch tương đối đồng nhất.

## 2. Giờ giao dịch

| Phiên              | Thời gian       | Loại                          |
| ------------------ | --------------- | ----------------------------- |
| Pre-open ATO       | 9:00–9:15       | Khớp lệnh định kỳ mở cửa      |
| Continuous AM      | 9:15–11:30      | Khớp lệnh liên tục            |
| **Nghỉ trưa**      | 11:30–13:00     | Không giao dịch               |
| Continuous PM      | 13:00–14:30     | Khớp lệnh liên tục            |
| Pre-close ATC      | 14:30–14:45     | Khớp lệnh định kỳ đóng cửa    |

> Có **gap giữa trưa** → minute-level data có khoảng trống. Daily data (project đang dùng) không bị ảnh hưởng.

## 3. Daily Price Limit ±7% (HOSE)

Mỗi cổ phiếu có **giá trần** (ceiling) và **giá sàn** (floor) cho phiên hôm sau:

$$P_{\text{ceiling}} = P_{\text{ref}} \times 1.07 \quad \text{(làm tròn)}$$
$$P_{\text{floor}}   = P_{\text{ref}} \times 0.93$$

Trong đó $P_{\text{ref}}$ = giá tham chiếu (thường là close hôm trước).

### Ảnh hưởng đến mô hình:

- **Distribution của log returns bị truncated** ở ±7% (≈ ±0.0676 log return)
- Mô hình giả định normal distribution sẽ over-estimate phần đuôi
- **Khi cổ phiếu chạm trần/sàn → liquidity giảm mạnh, dữ liệu kém tin cậy**

> So sánh: NYSE/NASDAQ không có price limit cố định (có circuit breakers ở mức 7%, 13%, 20% nhưng cho cả market).

## 4. Lot Size

- HOSE: **lot size = 100 cổ phiếu** (không khớp lệnh lẻ < 100)
- → Volume luôn là bội số của 100 (nhưng project dùng `volume` raw nên không ảnh hưởng modeling)

## 5. T+2 / T+2.5 Settlement

Mua cổ phiếu hôm T → nhận cổ phiếu vào chiều **T+2** (theo quy định mới từ 2024). Trước đó là T+2.5.

> Không ảnh hưởng directly đến forecasting daily close, nhưng cần biết khi viết phần "trading strategy" hoặc backtest.

## 6. Tết Nguyên Đán — Vấn đề đặc thù VN lớn nhất

Đây là điểm **đặc thù VN** quan trọng nhất phải xử lý:

- **Ngày nghỉ:** ~7–9 ngày liên tiếp (~5 phiên giao dịch bị "mất")
- **Năm khác nhau:** ngày Tết âm lịch khác nhau (cuối tháng 1 đến giữa tháng 2)
- **Hiệu ứng:** thường có "January effect" trước Tết (volume tăng, giá tăng) và "post-Tet" (rút vốn, giá điều chỉnh)

### Cách xử lý:

| Cách                                              | Ưu                  | Nhược                                              |
| ------------------------------------------------- | ------------------- | -------------------------------------------------- |
| Bỏ qua (gap trong index)                          | Đơn giản            | LSTM/RNN coi 5 phiên gap như 1 phiên → sai          |
| Forward-fill close, volume = 0                    | Giữ regular index   | Tạo features sai                                    |
| Thêm feature `days_since_last_trade`              | Chính xác           | Phức tạp hơn                                        |
| Encode Tet như "holiday regressor" trong Prophet  | Tự nhiên            | Chỉ Prophet mới hỗ trợ trực tiếp                    |

> **Khuyến nghị cho project:** giữ gap như hiện tại (ngày không có trading row), document rõ trong báo cáo.  
> Cho **Prophet:** dùng `model.add_country_holidays(country_name='VN')`.

## 7. Sự kiện corporate ảnh hưởng giá

| Sự kiện                  | Ảnh hưởng giá                       |
| ------------------------ | ----------------------------------- |
| Chia cổ tức tiền         | Giá điều chỉnh giảm = số tiền chi trả/CP |
| Chia cổ phiếu thưởng     | Giá điều chỉnh giảm tỷ lệ           |
| Phát hành thêm           | Giá điều chỉnh giảm                 |
| Chia tách (stock split)  | Giá điều chỉnh chia tỷ lệ           |

> **Quan trọng:** dữ liệu từ `vnstock` / `yfinance` thường là **adjusted close** (đã điều chỉnh các sự kiện trên). Cần verify để tránh outlier giả.

## 8. Đặc trưng của 5 ticker trong project

| Ticker  | Tên công ty       | Ngành                         | Đặc điểm                                          |
| ------- | ----------------- | ----------------------------- | ------------------------------------------------- |
| **VCB** | Vietcombank       | Ngân hàng                     | Vốn hoá lớn nhất, biến động trung bình             |
| **FPT** | FPT Corporation   | Công nghệ                     | Tăng trưởng cao, biến động vừa                     |
| **HPG** | Hoà Phát          | Thép                          | Biến động theo chu kỳ commodity                    |
| **VIC** | Vingroup          | Bất động sản, tập đoàn        | Biến động cao, nhiều sự kiện corporate             |
| **VNM** | Vinamilk          | Tiêu dùng (sữa)               | Defensive, biến động thấp                          |

> 5 mã này được chọn vì cover được **5 ngành lớn của VN-Index** → cho phép so sánh model performance qua các đặc tính ngành khác nhau.

## 9. Dữ liệu nguồn

| Source                  | Ưu                                     | Nhược                                  |
| ----------------------- | -------------------------------------- | -------------------------------------- |
| **vnstock**             | Local-friendly, intraday, miễn phí     | API thay đổi thường                    |
| **yfinance** (`.VN`)    | Stable, quen thuộc quốc tế             | Chậm cập nhật giá Tết, intraday hạn chế |
| Bloomberg / Reuters     | Chuẩn nhất                              | Trả phí cao                             |

Project dùng `vnstock` (chính) + `yfinance` (fallback) → cân bằng giữa chất lượng và khả dụng.

## 10. Chỉ số tham chiếu

| Chỉ số       | Ý nghĩa                                              |
| ------------ | ---------------------------------------------------- |
| **VN-Index** | Chỉ số tổng hợp của HOSE — đại diện thị trường VN    |
| **VN30**     | Top 30 cổ phiếu vốn hoá lớn nhất HOSE                |
| **HNX-Index**| Chỉ số HNX                                            |
| **UPCoM-Index** | Chỉ số UPCoM                                       |

> **5 ticker của project đều thuộc VN30** → có liquidity cao, ít gặp vấn đề data missing.

## Liên kết

- [01_data_ohlcv.md](01_data_ohlcv.md) — Format dữ liệu giá
- [05_eda.md](05_eda.md) — EDA cho data VN (lưu ý seasonality)
- [09_pitfalls.md](09_pitfalls.md) — Outliers do price limit
