# 🔍 05 — EDA & Statistical Tests

EDA là nền tảng của Chapter 3. Mục đích: hiểu đặc tính dữ liệu trước khi mô hình hoá, và biện luận lựa chọn mô hình phù hợp.

## 1. Stationarity (Tính dừng)

Time series được gọi là **stationary** khi mean, variance, autocovariance không thay đổi theo thời gian. Hầu hết các mô hình statistical (ARIMA) yêu cầu chuỗi dừng.

### 1.1 ADF Test (Augmented Dickey-Fuller)

Null hypothesis (H₀): chuỗi **có unit root** → không dừng.

```python
from statsmodels.tsa.stattools import adfuller
result = adfuller(series.dropna())
print(f'ADF stat: {result[0]:.4f}, p-value: {result[1]:.4f}')
```

| Kết luận                    | Khi nào             |
| --------------------------- | ------------------- |
| Reject H₀ → **dừng**        | p-value < 0.05      |
| Fail to reject → **không dừng** | p-value ≥ 0.05  |

> Giá close của cổ phiếu **gần như luôn không dừng** (random walk). Sau khi lấy first difference (giá trị thay đổi từng phiên), thường trở thành dừng.

### 1.2 KPSS Test

Null hypothesis ngược lại với ADF: H₀ là chuỗi dừng.

```python
from statsmodels.tsa.stattools import kpss
stat, p, _, _ = kpss(series.dropna(), regression='c')
```

> **Best practice:** chạy cả ADF + KPSS để confirm. Nếu cả hai đồng ý chuỗi dừng → tin cậy hơn.

### 1.3 Differencing

Nếu không dừng:

- **First difference:** $\Delta y_t = y_t - y_{t-1}$ — biến giá thành chênh lệch giá
- **Log return:** $r_t = \ln(y_t / y_{t-1})$ — chuẩn hơn cho cổ phiếu vì invariant với scale
- **Order of integration `d`** = số lần phải differencing → là tham số `d` trong ARIMA(p, d, q)

## 2. Autocorrelation — ACF & PACF

Cốt lõi để chọn (p, q) cho ARIMA.

### 2.1 ACF (Autocorrelation Function)

Đo correlation giữa $y_t$ và $y_{t-k}$ cho mọi lag $k$.

### 2.2 PACF (Partial ACF)

Đo correlation giữa $y_t$ và $y_{t-k}$ **sau khi loại bỏ ảnh hưởng** của các lag trung gian (1, 2, ..., k-1).

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
plot_acf(series, lags=40)
plot_pacf(series, lags=40)
```

### 2.3 Quy tắc chọn (p, q) cho ARIMA

| Pattern                              | Model       | Tham số          |
| ------------------------------------ | ----------- | ---------------- |
| ACF tail off, PACF cuts off at lag p | AR(p)       | ARIMA(p, d, 0)   |
| ACF cuts off at lag q, PACF tail off | MA(q)       | ARIMA(0, d, q)   |
| Cả hai đều tail off                  | ARMA(p, q)  | ARIMA(p, d, q)   |

> "Cuts off" = drop về gần 0 và ở trong dải confidence sau lag k.  
> "Tail off" = giảm dần dần theo exponential.

## 3. Seasonal Decomposition

Tách time series thành 3 thành phần:

$$y_t = T_t + S_t + R_t \quad \text{(additive)}$$
$$y_t = T_t \times S_t \times R_t \quad \text{(multiplicative)}$$

Trong đó:
- $T_t$: trend (xu hướng dài hạn)
- $S_t$: seasonality (chu kỳ)
- $R_t$: residual (nhiễu)

```python
from statsmodels.tsa.seasonal import seasonal_decompose
result = seasonal_decompose(series, model='additive', period=252)  # 252 ≈ 1 năm giao dịch
result.plot()
```

> **Lưu ý cho cổ phiếu VN:** seasonality không rõ rệt như sản phẩm bán lẻ; nhưng có thể có hiệu ứng cuối năm tài chính, hiệu ứng tháng giêng.

## 4. Returns vs Price

Trong nghiên cứu tài chính, **returns** thường được dùng thay cho price vì có tính chất tốt hơn:

| Quantity          | Công thức                              | Ưu điểm                                                          |
| ----------------- | -------------------------------------- | ---------------------------------------------------------------- |
| **Simple return** | $r_t = (P_t - P_{t-1}) / P_{t-1}$      | Trực quan                                                        |
| **Log return**    | $r_t = \ln(P_t / P_{t-1})$             | **Cộng được:** $r_{[t_1,t_2]} = \sum r_t$; gần normal distribution; đối xứng |

> **Quan trọng:** mô hình dự báo có thể dự đoán **return** thay vì **price** trực tiếp, sau đó convert ngược lại. Cách này thường ổn định hơn vì returns gần stationary.

## 5. Distribution Analysis

### 5.1 Skewness & Kurtosis

| Metric    | Ý nghĩa                | Giá trị bình thường        |
| --------- | ---------------------- | -------------------------- |
| Skewness  | Độ lệch của phân phối  | 0 (symmetric)              |
| Kurtosis  | Đuôi nặng nhẹ          | 3 (normal); >3 = heavy tails |

> Returns cổ phiếu thường có **negative skewness** (đuôi trái dài hơn — sụt giảm mạnh xảy ra nhiều hơn tăng mạnh) và **excess kurtosis** (đuôi nặng — outlier nhiều hơn normal).

### 5.2 Normality Tests

- **Jarque-Bera test:** dựa trên skewness & kurtosis
- **Shapiro-Wilk:** mạnh với mẫu nhỏ (< 5000)
- **Q-Q plot:** trực quan hoá độ lệch khỏi normal

```python
from scipy.stats import jarque_bera
stat, p = jarque_bera(returns.dropna())
```

> Returns cổ phiếu **gần như luôn không follow normal**. Đây là lý do nhiều mô hình giả định normal cho ra kết quả không tốt khi dùng trực tiếp.

## 6. Outlier Detection

### Phương pháp phổ biến

| Phương pháp                    | Ngưỡng                                       |
| ------------------------------ | -------------------------------------------- |
| Z-score                        | \|z\| > 3                                    |
| IQR (interquartile range)      | x < Q1 − 1.5·IQR hoặc x > Q3 + 1.5·IQR       |
| Modified Z-score (median-based) | \|MAD-z\| > 3.5                            |

> **Cẩn thận với cổ phiếu:** giá trần/sàn ±7% và sự kiện chia tách cổ phiếu (split) tạo ra "outliers" hợp lệ — không nên xoá bỏ mù quáng. Xem [08_vn_market.md § Daily Price Limit](08_vn_market.md).

## 7. Heatmap Correlation

Khi có nhiều technical indicators, vẽ heatmap để phát hiện multicollinearity:

```python
import seaborn as sns
features = ['close', 'ma_5', 'ma_20', 'rsi_14', 'macd', 'bb_upper', 'volume']
sns.heatmap(df[features].corr(), annot=True, cmap='coolwarm', center=0)
```

> Indicators như `ma_5`, `ma_20`, `bb_middle`, `close` thường có correlation > 0.95 → nếu dùng cho Linear Regression cần xử lý multicollinearity (PCA hoặc bỏ bớt feature trùng lặp).

## 8. Rolling Statistics

Quan sát mean và std qua thời gian để xác nhận stationarity bằng mắt thường:

```python
rolling_mean = series.rolling(window=50).mean()
rolling_std  = series.rolling(window=50).std()
```

Nếu rolling mean/std thay đổi rõ rệt theo thời gian → chuỗi không dừng.

## 9. Checklist cho Chapter 3 (EDA)

- [ ] Time plot của giá close cho mỗi ticker (5 plots)
- [ ] Time plot của volume + correlation với giá
- [ ] ADF + KPSS test cho price và log return (mỗi ticker)
- [ ] ACF & PACF plots (cho price và log return)
- [ ] Seasonal decomposition cho 1–2 ticker đại diện
- [ ] Distribution histogram + Q-Q plot của log returns
- [ ] Skewness, kurtosis, Jarque-Bera test (bảng tổng hợp)
- [ ] Heatmap correlation giữa các features (technical indicators)
- [ ] Rolling statistics (mean, std với window 20/50)
- [ ] Outlier detection report (số lượng outlier mỗi ticker)
- [ ] Bảng tóm tắt: với mỗi ticker, mean/std/min/max/skew/kurt của log return

## Liên kết

- [01_data_ohlcv.md](01_data_ohlcv.md) — Đặc tính của giá cổ phiếu
- [07_models.md § ARIMA](07_models.md) — Cách dùng ACF/PACF chọn (p, d, q)
- [09_pitfalls.md § Spurious regression](09_pitfalls.md) — Cẩn thận với non-stationary data
