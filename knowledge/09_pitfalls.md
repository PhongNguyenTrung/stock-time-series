# ⚠️ 09 — Pitfalls & Best Practices

Những lỗi thường gặp khi làm time series forecasting — đặc biệt với cổ phiếu. Reviewer/giáo viên hay vặn vào những điểm này.

## 1. Look-ahead Bias (Sai lệch nhìn trộm tương lai)

**Lỗi:** dùng thông tin tại thời điểm $t' > t$ khi predict $y_t$.

### Ví dụ vi phạm:

```python
# ❌ SAI: scale toàn bộ data trước khi split
scaler.fit(all_data)            # fit dùng cả test data!
X_train = scaler.transform(train)
X_test  = scaler.transform(test)
```

```python
# ✅ ĐÚNG: chỉ fit trên train
scaler.fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s  = scaler.transform(X_test)
```

### Các trường hợp dễ mắc:

- Imputation (fill NA) trên toàn bộ data
- Feature selection dùng correlation tính trên cả test
- Hyperparameter tuning với CV không tôn trọng thứ tự
- Rolling statistics tính từ "tương lai" (e.g., MA centered thay vì trailing)

> **Quy tắc vàng:** nhắm mắt và tự hỏi: "Ở thời điểm trading thực tế, mình có thông tin này không?" Nếu không → là look-ahead.

## 2. Spurious Regression

R² rất cao nhưng kết quả vô nghĩa khi cả X và y đều non-stationary và đều có trend.

### Ví dụ điển hình:

Regress giá VCB lên giá BTC sẽ có R² cao bất thường — không phải vì có quan hệ, mà vì cả hai đều có upward trend trong khoảng thời gian khảo sát.

### Cách phòng:

- Test stationarity trước khi regression (xem [05_eda.md](05_eda.md))
- Dùng **first-difference** hoặc **log returns** thay vì price
- Báo cáo Durbin-Watson statistic (test autocorrelation của residuals)

> Nếu R² > 0.95 trên cổ phiếu, nên cảnh giác — có thể là model chỉ học theo trend chung.

## 3. Overfitting trên test set nhỏ

- Test set 70/30 = 795 phiên; 80/20 = 530 phiên
- Tune hyperparameter dựa trên test RMSE → bị **leakage gián tiếp**

### Cách đúng:

```
Train [1] → Validation [2] → Test [3] (final)
```

Tune trên validation, **chỉ chạy test 1 lần duy nhất** ở cuối.

> **Trong project hiện tại:** chỉ có train/test (không có validation). Khuyến nghị member khi tune nên cắt thêm 10–15% cuối train làm validation, không động vào test.

## 4. Multiple Testing Problem

So sánh 7 mô hình × 5 tickers × 2 splits = **70 phép so sánh**. Xác suất ít nhất một so sánh "trông có ý nghĩa" tăng vọt.

### Hệ quả:

Một kết luận kiểu "Model X tốt hơn Model Y trên ticker Z" có thể chỉ là noise.

### Giải pháp đơn giản:

- **Bonferroni correction:** ngưỡng p-value chia cho số lần test
- Báo cáo ranking trung bình (average rank) qua tất cả ticker × split, thay vì kết luận cụ thể
- Trong báo cáo, dùng câu thận trọng: "Trên dữ liệu này, model X có xu hướng outperform Y" thay vì khẳng định

## 5. Stationarity Assumption Violation

Hầu hết mô hình statistical (Linear Regression, ARIMA, SVR) giả định:
- Residuals độc lập, identically distributed (i.i.d.)
- Có phương sai đồng nhất (homoscedastic)

### Cách kiểm tra residuals:

```python
import statsmodels.api as sm
sm.graphics.tsa.plot_acf(residuals)        # autocorrelation residuals
sm.stats.diagnostic.het_breuschpagan(...)  # heteroscedasticity test
```

> Nếu residuals còn autocorrelated → mô hình chưa capture hết structure → nên thử model phức tạp hơn hoặc thêm lag feature.

## 6. Improper Train/Test Split

❌ **Sai:** `train_test_split(X, y, shuffle=True)` — phá thứ tự thời gian.

✅ **Đúng:** split theo thời gian, mọi sample trong test phải có ngày sau mọi sample trong train.

> Project đã làm đúng (split theo cut date) — đảm bảo member khác cũng không sai khi load CSV. Xem [03_split.md](03_split.md).

## 7. Not Inverse-transforming Predictions

Khi dùng MinMaxScaler/StandardScaler:

```python
# ❌ SAI: tính RMSE trên scaled data
rmse = mean_squared_error(y_test_scaled, y_pred_scaled, squared=False)

# ✅ ĐÚNG: inverse trước
y_test_orig = scaler.inverse_transform(y_test_scaled)
y_pred_orig = scaler.inverse_transform(y_pred_scaled)
rmse = mean_squared_error(y_test_orig, y_pred_orig, squared=False)
```

> Số RMSE phải đối chiếu được với giá thực tế (đơn vị VND × 1000) để có ý nghĩa.

## 8. Survivorship Bias

Project chọn 5 cổ phiếu **hiện tại còn niêm yết** và có lịch sử dài. Các công ty đã hủy niêm yết / phá sản không được xét → kết quả lạc quan hơn thực tế.

> Không thể tránh hoàn toàn trong scope project sinh viên, nhưng nên **mention trong limitations** của báo cáo.

## 9. Reproducibility

❌ Code không có random seed → kết quả khác nhau mỗi lần chạy.

✅ Đặt seed cho mọi nguồn ngẫu nhiên:

```python
import random, numpy as np
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Keras/TF
import tensorflow as tf
tf.random.set_seed(SEED)

# PyTorch
import torch
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
```

> **Quy ước trong team:** dùng `SEED = 42` đồng nhất cho mọi model.

## 10. Reporting Pitfalls

Khi viết báo cáo:

- ❌ Báo cáo chỉ best result → cherry-picking
- ✅ Báo cáo trung bình ± std qua nhiều run (cho deep learning)
- ❌ Format số khác nhau giữa các bảng (3 vs 4 decimal places)
- ✅ Quy ước thống nhất: RMSE/MAE/R² 4dp, MAPE 3dp (theo [04_metrics.md](04_metrics.md))
- ❌ So sánh apples-to-oranges (mỗi model dùng feature khác nhau)
- ✅ Document rõ feature set của mỗi model

## 11. VN-specific Pitfalls

- ❌ Bỏ qua Tết Nguyên Đán → LSTM coi gap 5 phiên như 1 phiên
- ❌ Coi giá chạm trần/sàn ±7% là outlier → xoá nhầm dữ liệu hợp lệ
- ❌ Dùng holiday calendar Mỹ trong Prophet
- ✅ `model.add_country_holidays(country_name='VN')`
- ✅ Verify adjusted close (đã handle chia tách / cổ tức) trước khi train

Xem [08_vn_market.md](08_vn_market.md) để biết chi tiết.

## Checklist trước khi submit

- [ ] Mọi model dùng cùng split, cùng test set
- [ ] Không có look-ahead bias trong scaling/imputation/feature engineering
- [ ] **Naive baseline** có trong bảng so sánh (xem [06_evaluation.md](06_evaluation.md))
- [ ] Random seed cố định (SEED = 42)
- [ ] Predictions inverse-transformed về đơn vị gốc
- [ ] Residuals đã được kiểm tra (ACF + heteroscedasticity)
- [ ] Skill score vs Naive được tính
- [ ] Limitations và future work được nêu rõ
- [ ] Tết Nguyên Đán được handle hoặc document
- [ ] Tất cả số trong báo cáo có cùng format (4dp / 3dp như quy ước)

## Liên kết

- [03_split.md](03_split.md) — Split đúng cách
- [05_eda.md](05_eda.md) — Test stationarity
- [06_evaluation.md](06_evaluation.md) — Naive baseline & skill score
- [08_vn_market.md](08_vn_market.md) — VN-specific issues
