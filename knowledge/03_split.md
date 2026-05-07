# ✂️ 03 — Train / Test Split cho Time Series

Khác với dữ liệu thông thường, time series **không được shuffle** — phải giữ thứ tự thời gian để tránh data leakage (mô hình "nhìn trộm tương lai"). Xem [09_pitfalls.md § Look-ahead bias](09_pitfalls.md).

## Cấu hình split trong project

| Split  | Tỷ lệ      | Train end   | Test start  | Train rows | Test rows |
| ------ | ---------- | ----------- | ----------- | ---------- | --------- |
| `70_30`| 70% / 30%  | 2023-02-20  | 2023-02-21  | 1 853      | 795       |
| `80_20`| 80% / 20%  | 2024-03-12  | 2024-03-13  | 2 118      | 530       |

Cả hai split đều có **cùng cut date cho mọi ticker** → đảm bảo so sánh công bằng giữa các mã.

## Tại sao 2 cấu hình split?

- **70/30:** test set lớn hơn → đánh giá ổn định hơn, nhưng train ít hơn → mô hình có thể chưa đủ thông tin
- **80/20:** train nhiều hơn → mô hình học tốt hơn, nhưng test set nhỏ → metric dao động nhiều hơn
- So sánh **performance cùng một model qua 2 split** giúp kiểm tra **độ ổn định (robustness)** của mô hình

## Quy tắc bất di bất dịch

❌ **TUYỆT ĐỐI KHÔNG:**
- Dùng `train_test_split(X, y, shuffle=True)` với time series
- K-Fold cross-validation thông thường (random shuffle)
- Fit scaler/imputer trên toàn bộ data trước khi split

✅ **PHẢI LÀM:**
- Split theo thời gian: mọi sample trong test có ngày sau mọi sample trong train
- Fit scaler/imputer **chỉ trên train**, transform cả train và test
- Nếu cần validation: cắt thêm 10–15% cuối train làm validation

## Sơ đồ split chuẩn

```
Time →────────────────────────────────────────────────────────→
[─────────── Train ────────────][─── Validation ───][── Test ──]
        (~80% của 80% data)         (10–15% cuối train)   (20% cuối)
```

Trong project: chưa tách validation. Khi member tune hyperparameter, **không được tune trên test set** — phải tự cắt validation từ train.

## Walk-forward (advanced)

Project hiện tại dùng **static split** (1 lần cut). Để đánh giá nghiêm ngặt hơn nên dùng walk-forward — xem [06_evaluation.md § Walk-Forward Validation](06_evaluation.md).

## File output

Sau khi split, mỗi ticker × mỗi cấu hình tạo ra 2 file:

```
data/processed/splits/
├── 70_30/
│   ├── VCB_train.csv   ← 1 853 rows
│   ├── VCB_test.csv    ←   795 rows
│   ├── FPT_train.csv
│   ├── FPT_test.csv
│   └── ...             ← 5 tickers × 2 = 10 files
├── 80_20/
│   └── ...             ← 10 files
└── split_info.json     ← cut dates per ticker
```

## Liên kết

- [04_metrics.md](04_metrics.md) — Cách tính metrics trên test set
- [06_evaluation.md](06_evaluation.md) — Walk-forward validation và CV cho time series
- [09_pitfalls.md](09_pitfalls.md) — Các lỗi liên quan đến split
