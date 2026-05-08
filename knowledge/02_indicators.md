# 📈 02 — Technical Indicators

Các chỉ báo kỹ thuật được tính từ OHLCV và dùng làm **feature** cho mô hình. Trong project này, feature engineering ở `src/features.py` (gold layer, sau khi `src/clean.py` đã xử lý silver layer) tạo ra các indicators sau.

## 1. Moving Average (MA) — Đường trung bình động

Trung bình giá đóng cửa trong N phiên gần nhất.

```
MA_N(t) = (close[t-N+1] + close[t-N+2] + ... + close[t]) / N
```

| Indicator | Window | Ý nghĩa                                          |
| --------- | ------ | ------------------------------------------------ |
| `ma_5`    | 5      | Xu hướng ngắn hạn (~1 tuần giao dịch)            |
| `ma_20`   | 20     | Xu hướng trung hạn (~1 tháng giao dịch)          |
| `ma_50`   | 50     | Xu hướng dài hạn (~2.5 tháng giao dịch)          |

**Ứng dụng:** giá cắt lên đường MA → tín hiệu tăng; cắt xuống → tín hiệu giảm. Khi `ma_5 > ma_20 > ma_50` → xu hướng tăng mạnh.

## 2. RSI — Relative Strength Index

Đo động lượng (momentum), giá trị trong khoảng [0, 100].

```
RSI = 100 − 100 / (1 + RS)
RS  = Average Gain / Average Loss   (trên 14 phiên gần nhất)
```

| Vùng RSI | Ý nghĩa                                       |
| -------- | --------------------------------------------- |
| > 70     | Quá mua (overbought) — có thể đảo chiều giảm  |
| 30–70    | Vùng trung tính                                |
| < 30     | Quá bán (oversold) — có thể đảo chiều tăng    |

Trong project: `rsi_14` (window = 14 phiên, theo chuẩn Wilder).

## 3. MACD — Moving Average Convergence Divergence

Đo sự chênh lệch giữa hai EMA (Exponential Moving Average).

```
MACD line   = EMA_12(close) − EMA_26(close)
Signal line = EMA_9(MACD line)
Histogram   = MACD line − Signal line
```

| Trường        | Ý nghĩa                                                 |
| ------------- | ------------------------------------------------------- |
| `macd`        | Đường MACD (chênh lệch EMA 12 và EMA 26)                |
| `macd_signal` | Đường tín hiệu (EMA 9 của MACD)                         |
| `macd_hist`   | Histogram = MACD − Signal — đo độ mạnh của tín hiệu     |

**Tín hiệu mua/bán:** MACD cắt lên Signal → mua; cắt xuống → bán. Histogram dương và tăng → đà tăng mạnh.

## 4. Bollinger Bands

Đo độ biến động (volatility) quanh đường MA.

```
Middle band = MA_20(close)
Upper band  = Middle band + 2σ
Lower band  = Middle band − 2σ
```

(σ là độ lệch chuẩn của giá trong 20 phiên)

| Trường       | Ý nghĩa                                                                   |
| ------------ | ------------------------------------------------------------------------- |
| `bb_upper`   | Biên trên — giá vượt biên này thường được coi là quá mua                  |
| `bb_middle`  | Đường giữa = MA_20                                                        |
| `bb_lower`   | Biên dưới — giá xuống dưới biên này thường được coi là quá bán            |

**Đặc điểm:** băng hẹp (squeeze) → biến động thấp, sắp có biến động mạnh. Băng rộng → biến động đang cao.

## Khi nào dùng indicators làm feature?

| Mô hình           | Có dùng indicators không?                       |
| ----------------- | ----------------------------------------------- |
| Linear Regression | ✅ Có — nhiều feature giúp model tuyến tính học tốt hơn |
| ARIMA             | ❌ Không — chỉ dùng giá close (univariate)       |
| Prophet           | ❌ Không bắt buộc — Prophet tự decompose          |
| SVR               | ✅ Có — kết hợp tốt với indicators               |
| LSTM/GRU          | ✅ Có — feed cùng close làm multivariate input   |
| XGBoost           | ✅ Bắt buộc — tabular model cần feature engineering |
| Transformer       | ✅ Có                                            |

> **Cảnh báo:** indicators có **multicollinearity** cao (ma_5 và ma_20 tương quan mạnh). Với mô hình tuyến tính, nên check VIF (Variance Inflation Factor) hoặc dùng PCA. Với tree-based (XGBoost) thì không sao.

## Liên kết

- [01_data_ohlcv.md](01_data_ohlcv.md) — Dữ liệu nguồn để tính indicators
- [07_models.md](07_models.md) — Cách dùng indicators trong từng mô hình
