# ⚖️ 06 — Evaluation Methodology

Cách đánh giá mô hình ảnh hưởng trực tiếp đến tính học thuật và độ tin cậy của báo cáo. Reviewer/giáo viên thường xoáy vào phần này.

## 1. Naive Baseline (Random Walk)

Baseline đơn giản nhất: dự đoán giá phiên kế tiếp = giá phiên hiện tại.

$$\hat{y}_{t+1} = y_t$$

> **Tại sao quan trọng?** Giá cổ phiếu gần với random walk → naive baseline cực kỳ khó đánh bại. Bất kỳ mô hình nào không vượt được naive baseline → mô hình **vô giá trị**.

### Triển khai:

```python
# Naive: predicted[t] = actual[t-1]
y_pred_naive = y_test.shift(1).dropna()
y_true       = y_test[1:]
rmse_naive   = ((y_true - y_pred_naive) ** 2).mean() ** 0.5
```

> **Khuyến nghị mạnh:** thêm dòng "Naive" vào bảng so sánh Chapter 5. Nếu Linear Regression / ARIMA / LSTM đều thua naive → cần biện luận và xem lại pipeline.

## 2. Walk-Forward Validation (Rolling/Expanding Window)

Static train/test split (như project hiện tại) chỉ test một period duy nhất → đánh giá có thể bị bias.

**Walk-forward** mô phỏng quá trình dự báo thực tế:

```
Window 1: train [0..1000],  test [1001..1050]
Window 2: train [0..1050],  test [1051..1100]   ← expanding
Window 3: train [0..1100],  test [1101..1150]
...
```

| Loại         | Train window               | Khi nào dùng                                       |
| ------------ | -------------------------- | -------------------------------------------------- |
| **Expanding** | Lớn dần (giữ all history) | Dữ liệu ổn định, càng nhiều data càng tốt          |
| **Rolling**   | Cố định size, trượt       | Dữ liệu có concept drift, history cũ không liên quan |

```python
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    ...
```

> Project hiện tại dùng static split (70_30, 80_20) — phù hợp cho bài toán so sánh nhanh. Walk-forward là **future work** đáng giá để tăng độ tin cậy.

## 3. One-Step vs Multi-Step Forecasting

### One-step ahead

Dự đoán $\hat{y}_{t+1}$ dựa trên thông tin tới $t$. Sau đó dùng **giá thực tế** $y_{t+1}$ (không phải $\hat{y}_{t+1}$) để dự đoán $y_{t+2}$.

→ Dễ, sai số tích luỹ ít.

### Multi-step ahead

Dự đoán cả chuỗi $\hat{y}_{t+1}, \hat{y}_{t+2}, \ldots, \hat{y}_{t+h}$ chỉ với thông tin tới $t$.

| Strategy           | Mô tả                                                 | Trade-off          |
| ------------------ | ----------------------------------------------------- | ------------------ |
| **Recursive**      | Dùng prediction trước làm input cho prediction sau    | Sai số tích luỹ    |
| **Direct**         | Train h mô hình, mỗi mô hình cho một horizon          | Tốn tài nguyên     |
| **Multi-output**   | Một mô hình output cả vector h step                    | Phức tạp hơn       |

> **Project hiện tại:** dựa vào file CSV có cột `predicted` cho mỗi `date`, nhiều khả năng là **one-step ahead**. Cần xác minh và ghi rõ trong báo cáo Chapter 4.

## 4. Directional Accuracy

Trong giao dịch thực tế, **dự đoán đúng hướng** quan trọng hơn dự đoán đúng giá trị tuyệt đối.

$$DA = \frac{1}{n} \sum_{t=1}^{n} \mathbb{1}\left[\text{sign}(y_t - y_{t-1}) = \text{sign}(\hat{y}_t - y_{t-1})\right]$$

| Giá trị | Diễn giải                            |
| ------- | ------------------------------------ |
| 50%     | Đoán mò (random)                     |
| 55–60%  | Khá tốt                              |
| > 60%   | Rất tốt — hiếm với stock             |

```python
def directional_accuracy(y_true, y_pred, y_prev):
    actual_dir = np.sign(y_true - y_prev)
    pred_dir   = np.sign(y_pred - y_prev)
    return (actual_dir == pred_dir).mean()
```

> Đề xuất: thêm `Directional Accuracy` vào bảng metrics — sẽ tạo điểm nhấn cho báo cáo.

## 5. Skill Score (so với Naive)

$$SS = 1 - \frac{\text{RMSE}_{\text{model}}}{\text{RMSE}_{\text{naive}}}$$

| SS         | Diễn giải                       |
| ---------- | ------------------------------- |
| > 0        | Tốt hơn naive                   |
| = 0        | Bằng naive                      |
| < 0        | Tệ hơn naive — bỏ mô hình       |

> Skill score là **chỉ số quan trọng nhất** để chứng minh mô hình có giá trị. Một mô hình LSTM với RMSE nhỏ nhưng SS < 0 thực ra **vô dụng**.

## 6. Time Series Cross-Validation Pitfalls

❌ **Tuyệt đối không dùng K-Fold thông thường** (random shuffle) cho time series → leakage tương lai vào quá khứ.

✅ Phải dùng `TimeSeriesSplit` (sklearn) hoặc walk-forward.

```python
# ❌ SAI
from sklearn.model_selection import KFold
kfold = KFold(n_splits=5, shuffle=True)

# ✅ ĐÚNG
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
```

## 7. Statistical Significance

Khi so sánh 2 mô hình, RMSE_A < RMSE_B chưa chắc có ý nghĩa thống kê.

**Diebold-Mariano test:** kiểm định 2 forecast có sai khác có ý nghĩa hay không.

```python
# Pseudocode
from statsmodels.stats.diagnostic import acorr_ljungbox
# Hoặc lib chuyên: dieboldmariano
```

> Cao cấp — không bắt buộc trong project sinh viên, nhưng nên đề cập trong "Future work" của báo cáo. Xem [09_pitfalls.md § Multiple testing](09_pitfalls.md).

## 8. Bộ metrics đầy đủ đề xuất cho báo cáo

| Metric                        | Lý do nên có                                   |
| ----------------------------- | ---------------------------------------------- |
| RMSE                          | Penalty cho outlier                            |
| MAE                           | Sai số trung bình thực                         |
| MAPE                          | So sánh giữa ticker khác nhau                  |
| R²                            | Variance explained                             |
| **Directional Accuracy**      | Có ý nghĩa trading                             |
| **Skill Score (vs Naive)**    | Chứng minh model có giá trị                    |

## 9. Format bảng so sánh đề xuất (Chapter 5)

```
Ticker  Split   Model               RMSE    MAE     MAPE(%)  R²      DA(%)  SS
─────────────────────────────────────────────────────────────────────────────
VCB     70_30   Naive               0.94    0.62    1.05     0.945   50.2   0.000
VCB     70_30   Linear Regression   0.89    0.60    0.99     0.950   52.1   0.053
VCB     70_30   ARIMA              ...
VCB     70_30   LSTM               ...
...
```

> Đặt **Naive ở dòng đầu** mỗi nhóm để dễ so sánh skill score trực quan.

## 10. Robustness & Stability

Để chứng minh mô hình ổn định:

- Chạy cùng cấu hình **nhiều lần với seed khác nhau** (cho deep learning) → báo cáo mean ± std
- So sánh kết quả qua **2 split (70/30 và 80/20)** — đã có sẵn trong project
- Test trên **các giai đoạn thị trường khác nhau** (bull/bear) nếu chia được

## Liên kết

- [04_metrics.md](04_metrics.md) — Định nghĩa các metrics cơ bản
- [03_split.md](03_split.md) — Cách split tránh leakage
- [09_pitfalls.md](09_pitfalls.md) — Common mistakes trong evaluation
