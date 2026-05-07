# 📐 04 — Metrics đánh giá mô hình dự báo

Project dùng 4 metrics chuẩn cho regression/forecasting. Gọi:

- $y_i$ = giá trị thực tế (actual)
- $\hat{y}_i$ = giá trị dự đoán (predicted)
- $\bar{y}$ = trung bình giá trị thực tế
- $n$ = số quan sát trong test set

## 1. RMSE — Root Mean Squared Error

$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$

| Đặc điểm | Mô tả                                                              |
| -------- | ------------------------------------------------------------------ |
| Đơn vị   | **Cùng đơn vị với target** (VND × 1000)                            |
| Khoảng   | $[0, +\infty)$ — càng nhỏ càng tốt                                 |
| Nhạy với | **Outliers** — sai số lớn bị bình phương → ảnh hưởng mạnh đến RMSE |
| Ứng dụng | Khi muốn phạt nặng các dự đoán sai lệch lớn                        |

> **Ví dụ trong project:** VCB split 70/30, RMSE = 0.89 → trung bình mô hình sai khoảng 890 VND/cổ phiếu.

## 2. MAE — Mean Absolute Error

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$

| Đặc điểm | Mô tả                                                            |
| -------- | ---------------------------------------------------------------- |
| Đơn vị   | **Cùng đơn vị với target** (VND × 1000)                          |
| Khoảng   | $[0, +\infty)$ — càng nhỏ càng tốt                               |
| Nhạy với | **Robust với outliers** hơn RMSE                                 |
| Ứng dụng | Khi muốn thước đo sai số "trung bình thực sự", không bị méo bởi outlier |

> **Quan hệ với RMSE:** luôn có $\text{MAE} \le \text{RMSE}$. Khoảng cách giữa hai giá trị càng lớn → distribution của error càng có nhiều outlier.

## 3. MAPE — Mean Absolute Percentage Error

$$\text{MAPE} = \frac{100\%}{n} \sum_{i=1}^{n} \left|\frac{y_i - \hat{y}_i}{y_i}\right|$$

| Đặc điểm   | Mô tả                                                                  |
| ---------- | ---------------------------------------------------------------------- |
| Đơn vị     | **Phần trăm (%)** — không phụ thuộc thang đo của target                |
| Khoảng     | $[0\%, +\infty)$ — càng nhỏ càng tốt                                   |
| Ưu điểm    | **So sánh được giữa các ticker giá khác nhau** (VCB vs HPG, ...)       |
| Nhược điểm | Không xác định khi $y_i = 0$; bị lệch khi $y_i$ rất nhỏ                |

> **Quy tắc kinh nghiệm cho stock forecasting:**
> - MAPE < 1% → mô hình rất tốt
> - 1% – 5% → khá tốt, có thể dùng được
> - 5% – 10% → cần cải thiện
> - \> 10% → khả năng dự báo yếu

## 4. R² — Coefficient of Determination (Hệ số xác định)

$$R^2 = 1 - \frac{\sum_{i=1}^{n} (y_i - \hat{y}_i)^2}{\sum_{i=1}^{n} (y_i - \bar{y})^2}$$

| Đặc điểm   | Mô tả                                                                          |
| ---------- | ------------------------------------------------------------------------------ |
| Đơn vị     | **Không có đơn vị** (giá trị tỷ lệ)                                            |
| Khoảng     | $(-\infty, 1]$ — càng gần 1 càng tốt                                           |
| Diễn giải  | $R^2 = 0.95$ → mô hình giải thích được **95% phương sai** của giá thực tế      |
| Cảnh báo   | $R^2 < 0$ → mô hình **kém hơn cả việc dùng giá trung bình** để dự đoán         |

> **Quan trọng:** với time series có trend mạnh (như giá cổ phiếu dài hạn), $R^2$ có thể cao một cách "ảo" do mô hình chỉ học theo trend. Phải xem kèm RMSE/MAPE để đánh giá đúng. Xem [09_pitfalls.md § Spurious regression](09_pitfalls.md).

---

## Diễn giải metrics trong context cổ phiếu Việt Nam

### Cách đọc một bộ metric

Lấy ví dụ kết quả Linear Regression (split 70/30) trong project:

| Ticker | RMSE | MAE  | MAPE   | R²     | Giá close trung bình | Diễn giải                                            |
| ------ | ---- | ---- | ------ | ------ | -------------------- | ---------------------------------------------------- |
| FPT    | 1.63 | 1.14 | 1.242% | 0.9949 | ~80–110              | Sai trung bình ~1140 VND/cp, ~1.24% — rất tốt        |
| HPG    | 0.40 | 0.28 | 1.239% | 0.9865 | ~22–30               | Sai ~280 VND/cp — rất tốt                            |
| VCB    | 0.89 | 0.60 | 0.995% | 0.9501 | ~55–80               | Sai ~600 VND/cp, dưới 1% — xuất sắc                  |
| VIC    | 2.51 | 1.15 | 1.669% | 0.9971 | ~40–65               | RMSE cao, R² rất cao — có outliers                   |
| VNM    | 0.89 | 0.61 | 1.009% | 0.9476 | ~60–75               | Sai ~610 VND/cp — tốt                                |

### Khi nào RMSE và MAE chênh lệch nhiều?

VIC có RMSE = 2.51 nhưng MAE = 1.15 → khoảng cách 2.18×. Điều này gợi ý:

- Mô hình dự đoán **đa số phiên** với sai số nhỏ (~MAE)
- Nhưng có **một số phiên outlier** với sai số rất lớn → kéo RMSE lên cao
- Thường xảy ra khi có sự kiện bất thường (chia tách cổ phiếu, tin tức lớn, biến động mạnh)

### So sánh metrics đúng cách

- **Cùng ticker, khác model:** dùng RMSE/MAE/MAPE/R² đều OK
- **Khác ticker, cùng model:** ưu tiên **MAPE** và **R²** vì không phụ thuộc giá tuyệt đối
- **Cùng model, khác split:** so sánh để đánh giá robustness; RMSE chênh lệch nhiều giữa 70/30 và 80/20 → mô hình không ổn định

### Bộ metrics nên dùng trong báo cáo

> **Khuyến nghị:** luôn báo cáo **cả 4 metrics** vì mỗi metric phản ánh một góc khác nhau của sai số:
> - **RMSE** → độ lớn sai số (có phạt outlier)
> - **MAE** → độ lớn sai số (trung bình thực)
> - **MAPE** → sai số tương đối (%)
> - **R²** → khả năng giải thích phương sai
>
> Ngoài ra nên thêm **Naive baseline** và **Directional Accuracy** — xem [06_evaluation.md](06_evaluation.md).

---

## Quy ước cột trong CSV kết quả

| Cột          | Format        | Ví dụ                |
| ------------ | ------------- | -------------------- |
| `Ticker`     | string        | `VCB`                |
| `Split`      | `XX_YY`       | `70_30`, `80_20`     |
| `Model`      | string        | `Linear Regression`  |
| `RMSE`       | float, 4 dp   | `0.8900`             |
| `MAE`        | float, 4 dp   | `0.6000`             |
| `MAPE (%)`   | float, 3 dp   | `0.995`              |
| `R²`         | float, 4 dp   | `0.9501`             |

> **Lưu ý:** Tên cột `R²` dùng ký tự Unicode `²` (U+00B2), không phải `R^2` hay `R2` — cần encoding UTF-8 khi đọc/ghi CSV. Pandas:
> ```python
> df = pd.read_csv(path, encoding='utf-8')
> ```

## Liên kết

- [03_split.md](03_split.md) — Test set để tính metrics
- [06_evaluation.md](06_evaluation.md) — Naive baseline, directional accuracy, skill score
- [09_pitfalls.md](09_pitfalls.md) — Spurious regression, multiple testing
