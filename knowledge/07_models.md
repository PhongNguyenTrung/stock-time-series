# 🤖 07 — Model-specific Know-how

Tổng hợp kiến thức cốt lõi cho 7 mô hình dự báo trong dự án. Phục vụ Member 1 hỗ trợ Member 2/3/4 và viết Chapter 4.

## Tổng quan

Dự án so sánh 7 mô hình thuộc 3 nhóm:

| Nhóm                   | Model              | Member  | Đặc điểm                                                |
| ---------------------- | ------------------ | ------- | ------------------------------------------------------- |
| Statistical (cổ điển)  | Linear Regression  | 1       | Baseline tuyến tính với lag features                    |
|                        | ARIMA              | 2/3/4   | AutoRegressive Integrated Moving Average — chuẩn cho time series |
|                        | Prophet            | 2/3/4   | Facebook Prophet — chuyên decomposition trend + seasonality |
| Machine Learning       | SVR                | 2/3/4   | Support Vector Regression — kernel-based, robust với outliers |
|                        | XGBoost            | 2/3/4   | Gradient boosting — mạnh với tabular features          |
| Deep Learning          | LSTM               | 2/3/4   | Long Short-Term Memory — capture dependencies dài hạn   |
|                        | GRU                | 2/3/4   | Gated Recurrent Unit — đơn giản hơn LSTM, train nhanh hơn |
|                        | Transformer        | 2/3/4   | Self-attention — state-of-the-art cho sequence          |

---

## 1. Linear Regression (Member 1 — done)

- **Tham số chính:** không có (hoặc regularization với Ridge/Lasso)
- **Feature:** lag features (close[t-1], close[t-2], ..., close[t-k]) + technical indicators
- **Yêu cầu:** features không multicollinear; có thể dùng StandardScaler trước khi fit

```python
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X_train, y_train)
```

> Trong project: đã dùng lag features. Coefficients có thể interpret để hiểu feature nào quan trọng.

## 2. ARIMA — AutoRegressive Integrated Moving Average

Công thức: **ARIMA(p, d, q)**

- **p (AR order):** số lag của $y$ làm input
- **d (Differencing):** số lần lấy sai phân để chuỗi dừng
- **q (MA order):** số lag của error term

### Cách chọn (p, d, q):

1. **d:** dùng ADF test → nếu không dừng, lấy first difference, test lại. Số lần = `d`. Xem [05_eda.md § Stationarity](05_eda.md).
2. **p:** xem PACF — số lag đáng kể đầu tiên trước khi cut off
3. **q:** xem ACF — tương tự

### Auto-ARIMA:

```python
from pmdarima import auto_arima
model = auto_arima(y_train, seasonal=False, trace=True,
                   max_p=5, max_q=5, max_d=2, ic='aic')
```

> **Pitfall:** ARIMA dự đoán returns thường tốt hơn dự đoán price trực tiếp.

### SARIMA — ARIMA + Seasonal

ARIMA(p,d,q)(P,D,Q,s) — nếu data có seasonality. `s` = period (252 cho yearly).

## 3. SVR — Support Vector Regression

Kernel-based. Hyperparameters chính:

| Tham số   | Ý nghĩa                                  | Giá trị mặc định / khuyến nghị |
| --------- | ---------------------------------------- | ------------------------------ |
| `kernel`  | Hàm kernel                               | `'rbf'` (cho non-linear)       |
| `C`       | Regularization (lớn = ít regularization) | 1.0; tune trong [0.1, 100]     |
| `epsilon` | Vùng tolerance                           | 0.1; tỷ lệ với scale của y     |
| `gamma`   | Độ "lan" của RBF kernel                  | `'scale'`                      |

```python
from sklearn.svm import SVR
model = SVR(kernel='rbf', C=10, epsilon=0.1)
```

> **BẮT BUỘC:** scale features trước (StandardScaler/MinMaxScaler) — SVR cực kỳ nhạy với scale.

## 4. Prophet (Facebook)

Decompose time series thành: trend + seasonality + holidays + error.

```python
from prophet import Prophet
df = pd.DataFrame({'ds': dates, 'y': close_prices})
model = Prophet(
    changepoint_prior_scale=0.05,        # mức linh hoạt của trend
    seasonality_mode='multiplicative',   # cho stock thường tốt hơn additive
    yearly_seasonality=True,
)
model.add_country_holidays(country_name='VN')   # ⚠️ Tết Nguyên Đán quan trọng
model.fit(df)
```

| Tham số                      | Ý nghĩa                                                |
| ---------------------------- | ------------------------------------------------------ |
| `changepoint_prior_scale`    | Lớn → trend uốn nhiều; nhỏ → mượt                       |
| `seasonality_prior_scale`    | Tương tự cho seasonality                                |
| `seasonality_mode`           | `additive` hoặc `multiplicative`                        |

> **Ưu điểm:** robust, ít tune; **nhược điểm:** không capture được short-term dynamics tốt như LSTM.  
> **VN-specific:** nhớ thêm `add_country_holidays(country_name='VN')` để Prophet handle Tết.

## 5. LSTM — Long Short-Term Memory

Recurrent neural network giải quyết vanishing gradient của RNN thường.

### Hyperparameters chính:

| Tham số                    | Khuyến nghị                              |
| -------------------------- | ---------------------------------------- |
| `sequence_length` (lookback) | 30–60 (khoảng 1.5–3 tháng giao dịch)   |
| `hidden_units`             | 32–128                                   |
| `num_layers`               | 1–3                                      |
| `dropout`                  | 0.2–0.3                                  |
| `learning_rate`            | 0.001 (Adam)                             |
| `batch_size`               | 32–64                                    |
| `epochs`                   | 50–200, dùng EarlyStopping               |

### Pipeline chuẩn:

```python
# 1. Scale
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
data_scaled = scaler.fit_transform(data)   # ⚠️ chỉ fit trên train!

# 2. Tạo sequences (X: [n_samples, seq_len, n_features], y: [n_samples])
def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len, 0])  # predict close
    return np.array(X), np.array(y)

# 3. Model
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(seq_len, n_features)),
    Dropout(0.2),
    LSTM(32),
    Dropout(0.2),
    Dense(1),
])
model.compile(optimizer='adam', loss='mse')
```

> **Pitfall thường gặp:**
> - Quên scale data → loss không converge
> - Không inverse_transform khi tính metrics → metrics sai
> - Dùng `random_state` mặc định → không reproducible giữa các lần chạy
> - Fit scaler trên all data → look-ahead bias. Xem [09_pitfalls.md](09_pitfalls.md).

## 6. GRU — Gated Recurrent Unit

Tương tự LSTM nhưng đơn giản hơn (2 gate thay vì 3). Train nhanh hơn ~30%, performance thường tương đương trên dataset nhỏ.

```python
from tensorflow.keras.layers import GRU
model = Sequential([GRU(64, ...), ...])
```

> Trong project nhỏ như stock VN (~2600 phiên), **GRU thường tốt hơn LSTM** vì ít tham số → ít overfitting.

## 7. XGBoost

Gradient boosting với tabular data. Cực mạnh với feature engineering tốt.

### Feature engineering cho XGBoost:

- Lag features: `close[t-1]`, `close[t-5]`, `close[t-20]`
- Technical indicators: MA, RSI, MACD, BB (xem [02_indicators.md](02_indicators.md))
- Date features: `day_of_week`, `month`, `quarter`, `is_month_end`
- Rolling stats: rolling mean/std/min/max

### Hyperparameters chính:

| Tham số              | Default | Tune range  |
| -------------------- | ------- | ----------- |
| `n_estimators`       | 100     | 100–1000    |
| `max_depth`          | 6       | 3–10        |
| `learning_rate`      | 0.3     | 0.01–0.3    |
| `subsample`          | 1.0     | 0.6–1.0     |
| `colsample_bytree`   | 1.0     | 0.6–1.0     |

```python
import xgboost as xgb
model = xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05)
model.fit(X_train, y_train,
          eval_set=[(X_val, y_val)],
          early_stopping_rounds=20)
```

> **Lợi thế lớn:** built-in `feature_importances_` → đưa vào báo cáo để chứng minh feature nào quan trọng.

## 8. Transformer

State-of-the-art cho sequence modeling. Phức tạp hơn LSTM nhưng có thể vượt trội với data lớn.

### Components chính:

- **Self-attention:** capture dependencies ở mọi khoảng cách
- **Positional encoding:** vì attention không có sense thứ tự (khác với RNN)
- **Multi-head attention:** học nhiều "góc nhìn" cùng lúc

### Hyperparameters:

| Tham số                  | Khuyến nghị |
| ------------------------ | ----------- |
| `num_heads`              | 4–8         |
| `d_model` (embedding dim) | 64–256     |
| `num_layers`             | 2–6         |
| `dropout`                | 0.1         |

> **Cảnh báo:** Transformer cần nhiều data. Với ~2600 phiên/ticker, có nguy cơ overfitting cao. Khuyến nghị dùng kèm regularization mạnh hoặc transfer learning.

## 9. Bảng so sánh tổng quát

| Model       | Tốc độ train | Cần feature engineering | Capture long dependencies | Reproducibility | Phù hợp data size |
| ----------- | ------------ | ----------------------- | ------------------------- | --------------- | ----------------- |
| Linear      | ⭐⭐⭐⭐⭐    | ⭐⭐⭐                   | ⭐                         | ⭐⭐⭐⭐⭐         | Mọi size         |
| ARIMA       | ⭐⭐⭐⭐      | ⭐                       | ⭐⭐                        | ⭐⭐⭐⭐           | Nhỏ–TB           |
| Prophet     | ⭐⭐⭐⭐      | ⭐                       | ⭐⭐⭐                       | ⭐⭐⭐⭐           | Mọi size         |
| SVR         | ⭐⭐⭐        | ⭐⭐⭐                   | ⭐⭐                        | ⭐⭐⭐⭐           | Nhỏ–TB           |
| XGBoost     | ⭐⭐⭐        | ⭐⭐⭐⭐⭐                | ⭐⭐                        | ⭐⭐⭐             | TB–lớn           |
| LSTM/GRU    | ⭐⭐          | ⭐⭐                     | ⭐⭐⭐⭐                      | ⭐⭐               | TB–lớn           |
| Transformer | ⭐            | ⭐⭐                     | ⭐⭐⭐⭐⭐                    | ⭐⭐               | Lớn               |

## 10. Pipeline đánh giá chung

1. Mỗi member train mô hình trên tập train (70% hoặc 80%)
2. Dự báo trên tập test → lưu file `<model>_predictions.csv`
3. Tính 4 metrics → lưu file `<model>_metrics.csv`
4. Member 1 (Data Engineer) tổng hợp → bảng so sánh ở Chapter 5

CSV format chuẩn — xem [04_metrics.md § Quy ước CSV](04_metrics.md).

## Liên kết

- [02_indicators.md](02_indicators.md) — Features (MA, RSI, MACD, BB)
- [05_eda.md](05_eda.md) — Stationarity, ACF/PACF cho ARIMA
- [06_evaluation.md](06_evaluation.md) — Cách đánh giá cho mỗi model
- [09_pitfalls.md](09_pitfalls.md) — Lỗi thường gặp khi train deep learning
