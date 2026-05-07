<h1 align="center">📚 Knowledge Base</h1>

<p align="center">
  <i>Tài liệu tham chiếu cho dự án Vietnamese Stock Forecasting</i><br/>
  <b>Tickers:</b> VCB · FPT · HPG · VIC · VNM
</p>

---

## Mục lục

| #  | File                                          | Nội dung                                                       |
|----|-----------------------------------------------|----------------------------------------------------------------|
| 01 | [Dữ liệu OHLCV](01_data_ohlcv.md)             | Open/High/Low/Close/Volume — định dạng, đơn vị, đặc tính       |
| 02 | [Technical Indicators](02_indicators.md)      | MA, RSI, MACD, Bollinger Bands                                 |
| 03 | [Train/Test Split](03_split.md)               | 70_30 và 80_20, cut date, lý do chọn 2 cấu hình                |
| 04 | [Metrics đánh giá](04_metrics.md)             | RMSE, MAE, MAPE, R² — công thức, diễn giải, quy ước CSV        |
| 05 | [EDA & Statistical Tests](05_eda.md)          | ADF, KPSS, ACF/PACF, seasonal decomposition, returns analysis   |
| 06 | [Evaluation Methodology](06_evaluation.md)    | Naive baseline, walk-forward, directional accuracy, skill score |
| 07 | [Model-specific Know-how](07_models.md)       | ARIMA, Prophet, SVR, LSTM, GRU, XGBoost, Transformer            |
| 08 | [Thị trường CK Việt Nam](08_vn_market.md)     | HOSE/HNX, price limit ±7%, Tết, lot size, T+2.5 settlement      |
| 09 | [Pitfalls & Best Practices](09_pitfalls.md)   | Look-ahead bias, spurious regression, overfitting, reproducibility |

---

## Đối tượng sử dụng

- **Member 1 (Data Engineer & Report Coordinator):** tham chiếu khi xây pipeline, viết báo cáo, hỗ trợ team
- **Member 2/3/4 (Model Developers):** đọc trước khi implement model — đặc biệt mục 04, 06, 07
- **Reviewer / giáo viên:** quick reference các quy ước và quyết định kỹ thuật

## Thứ tự đề xuất đọc

### Cho người mới vào project
`01 → 02 → 03 → 04 → 08`  
(Hiểu data trước, rồi đến split, metrics, đặc thù VN)

### Cho member triển khai model
`04 → 06 → 07 → 09`  
(Metrics → cách đánh giá → model cụ thể → tránh lỗi)

### Cho viết Chapter 3 (EDA)
`01 → 02 → 05 → 08`

### Cho viết Chapter 4 (Models)
`07 → 04 → 06`

### Cho viết Chapter 5 (Comparison)
`04 → 06 → 09`

---

## Quy ước chung

- Tài liệu viết bằng **tiếng Việt + thuật ngữ chuyên ngành tiếng Anh**
- Công thức toán dùng **LaTeX inline** (`$...$`) hoặc block (`$$...$$`)
- Ví dụ code dùng **Python** (chuẩn của project)
- File tách độc lập — có thể đọc riêng từng file
- Cập nhật khi pipeline / quy ước thay đổi → đồng bộ với code

## Liên kết khác

- [README.md](../README.md) — Tổng quan dự án và pipeline
- [Dashboard](../docs/index.html) — Visualize kết quả model
- [Notebooks](../notebooks/) — `00_template.ipynb`, `01_linear_regression.ipynb`, `02_eda.ipynb`
