I. Cấu trúc chi tiết Tập lớn
Chương 1: Giới thiệu
Lý do chọn đề tài (Tầm quan trọng của dự báo chứng khoán).
Mục tiêu nghiên cứu và các câu hỏi nghiên cứu.
Phạm vi đề tài (Ví dụ: Dự báo chỉ số VN-Index hoặc mã cổ phiếu cụ thể trong 2 năm gần nhất).
Chương 2: Cơ sở lý thuyết & Tổng quan
Khái niệm về chuỗi thời gian (Tính dừng, tính mùa vụ, xu hướng).
Các mô hình truyền thống (ARIMA, SARIMA).
Các mô hình học máy và học sâu (SVR, Random Forest, LSTM, GRU, hoặc Transformer).
Các nghiên cứu liên quan trước đây.
Chương 3: Thu thập và Tiền xử lý dữ liệu (Data Preprocessing)
Nguồn dữ liệu (Yahoo Finance, Cafef, Vietstock...).
Làm sạch dữ liệu (Xử lý giá trị thiếu, nhiễu).
Kỹ thuật trích xuất đặc trưng (Feature Engineering): Các chỉ số kỹ thuật như MA, RSI, MACD, Bollinger Bands.
Chia tập dữ liệu (Train/Validation/Test) theo thời gian.
Chương 4: Đề xuất mô hình & Thực nghiệm (Methodology & Experiments)
Thiết kế kiến trúc các mô hình lựa chọn.
Quy trình huấn luyện và tinh chỉnh tham số (Hyperparameter Tuning).
Thiết lập các kịch bản thử nghiệm (Dự báo ngắn hạn với dài hạn).
Chương 5: Đánh giá & Thảo luận (Evaluation & Discussion)
Các chỉ số đo lường: $RMSE, MAE, MAPE, R^2$.
So sánh hiệu suất giữa các mô hình (Ví dụ: LSTM vs. Random Forest).
Trực quan hóa kết quả (Biểu đồ giá thực tế với dự báo).
Phân tích ý nghĩa kinh tế và hạn chế của mô hình.
Chương 6: Kết luận & Hướng phát triển
Tóm tắt kết quả đạt được.
Đề xuất hướng cải thiện (Thêm phân tích cảm tính từ tin tức, mạng xã hội).

II. Phân công công việc (Nhóm 4 người)
1. Phân công vai trò chi tiết
Thành viên 1: Data Engineer & Report Coordinator
Nhiệm vụ thu thập dữ liệu: Sử dụng các thư viện như vnstock hoặc yfinance để lấy dữ liệu lịch sử của 5 mã chứng khoán (ví dụ: VCB, FPT, HPG, VIC, VNM) trong khoảng 10 năm.
Tiền xử lý dùng chung: Làm sạch dữ liệu, xử lý giá trị thiếu và chia tập Train/Test thống nhất cho cả nhóm (chia train test theo từng nhóm (7-3, 8-2).
Tổng hợp báo cáo: Thu thập kết quả từ 3 thành viên còn lại để kẻ bảng so sánh tổng thể.
Viết chương: Chương 1 (Mở đầu), Chương 3 (Dữ liệu) và Chương 6 (Kết luận).
Thêm 1 model (tự chọn)
Thành viên 2: AI Engineer (Mô hình truyền thống & Học máy)
Model 1: ARIMA/SARIMA. (Mô hình thống kê cổ điển).
Model 2: Support Vector Regression (SVR) hoặc Random Forest.
Đầu ra: 10 biểu đồ dự báo (2 model × 5 mã) + Bảng chỉ số $RMSE, MAE$ cho các mã này.
Làm báo phần thuật toán của mình
Thành viên 3: Deep Learning Engineer (Mạng nơ-ron chuỗi)
Model 3: LSTM (Long Short-Term Memory).
Model 4: GRU (Gated Recurrent Unit).
Đầu ra: 10 biểu đồ dự báo (2 model × 5 mã) + Bảng chỉ số $RMSE, MAE$ cho các mã này.
Làm báo phần thuật toán của mình
Thành viên 4: Advanced AI Engineer (Mô hình hiện đại)
Model 5: Facebook Prophet (Mô hình mạnh mẽ cho dữ liệu có tính mùa vụ).
Model 6: XGBoost hoặc Transformer.
Đầu ra: 10 biểu đồ dự báo (2 model × 5 mã) + Bảng chỉ số $RMSE, MAE$ cho các mã này.
Làm báo phần thuật toán của mình

2. Quy trình thực hiện và Tổng kết
Bước 1: Thống nhất các mã chứng khoán & Chỉ số
Thành viên 1 cung cấp file CSV sạch của 5 mã. Cả nhóm thống nhất dùng giá đóng cửa (Close Price) để dự báo và dùng $RMSE, MAE$ làm thước đo.
Bước 2: Triển khai Model & Vẽ biểu đồ
Mỗi thành viên (2, 3, 4) khi chạy xong phải vẽ biểu đồ so sánh: Giá thực tế (Actual) vs Giá dự báo (Predicted) trên cùng một trục tọa độ cho mỗi mã.
Bước 3: Tổng hợp bảng so sánh (Thành viên 1 thực hiện)
Thành viên 1 sẽ lập bảng tổng hợp cuối cùng để đưa vào chương 5 của báo cáo. Ví dụ mẫu cho 1 mã chứng khoán:


