# 📊 01 — Dữ liệu giá cổ phiếu (OHLCV)

OHLCV là 5 giá trị cơ bản mô tả hoạt động của một cổ phiếu trong một phiên giao dịch.

| Trường  | Tên đầy đủ    | Ý nghĩa                                                          | Đơn vị               |
| ------- | ------------- | ---------------------------------------------------------------- | -------------------- |
| `open`  | Giá mở cửa    | Giá khớp lệnh đầu tiên trong phiên                                | VND × 1000           |
| `high`  | Giá cao nhất  | Mức giá cao nhất đạt được trong phiên                             | VND × 1000           |
| `low`   | Giá thấp nhất | Mức giá thấp nhất chạm tới trong phiên                            | VND × 1000           |
| `close` | Giá đóng cửa  | Giá khớp lệnh cuối cùng — **giá trị mục tiêu (target) cho dự báo** | VND × 1000           |
| `volume`| Khối lượng    | Tổng số cổ phiếu được khớp lệnh trong phiên                       | Cổ phiếu (số lượng)  |

## Tại sao chọn `close` làm target?

- `close` là giá tham chiếu cho phiên kế tiếp → có ý nghĩa giao dịch thực tế
- Phản ánh sự đồng thuận cuối phiên giữa người mua và người bán
- Ít bị ảnh hưởng bởi nhiễu trong phiên (intraday noise) so với `open` / `high` / `low`
- Quy ước chuẩn trong nghiên cứu time series forecasting

## Đặc tính của giá cổ phiếu

- **Phi dừng (non-stationary):** trung bình và phương sai thay đổi theo thời gian → cần kiểm tra ADF test, có thể cần lấy sai phân (differencing) trước khi mô hình hoá với ARIMA. Xem [05_eda.md](05_eda.md).
- **Có xu hướng (trend):** thường tăng/giảm dài hạn theo chu kỳ kinh tế
- **Có biến động (volatility clustering):** các giai đoạn biến động cao thường đi kèm nhau
- **Random walk:** thay đổi giá ngắn hạn rất khó dự đoán — đây là lý do RMSE thường không xuống dưới một ngưỡng nhất định

## Đơn vị giá cổ phiếu

- **VND × 1000** (nghìn VND)
- Ví dụ: `close = 52.29` → giá thực tế là **52 290 VND/cổ phiếu**
- Lý do: tránh số quá lớn trong mô hình (ổn định khi training neural network)

## Đơn vị thời gian

- **1 phiên giao dịch = 1 ngày làm việc** (Mon–Fri, không tính lễ Tết và ngày sàn nghỉ)
- ~252 phiên/năm (chuẩn quốc tế); thực tế Việt Nam ~250 phiên/năm
- Window MA-5 ≈ 1 tuần; MA-20 ≈ 1 tháng; MA-50 ≈ 2.5 tháng

## Liên kết

- [02_indicators.md](02_indicators.md) — Technical indicators được tính từ OHLCV
- [08_vn_market.md](08_vn_market.md) — Đặc thù thị trường VN (Tết, price limit, ...)
