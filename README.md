# HỆ THỐNG QUẢN LÝ THỰC ĐƠN & SỔ KIỂM THỰC 3 BƯỚC (QĐ 1246/QĐ-BYT)

Hệ thống ứng dụng Web hoàn chỉnh thay thế và nâng cấp toàn diện file Excel `LƯU_MẪU_MASTER.xlsx`, giúp công tác quản lý suất ăn, kiểm thực ba bước và lưu mẫu thức ăn cho bếp ăn tập thể / công ty trở nên **dễ dàng, trực quan và tự động hóa 100%** theo đúng quy định của Bộ Y Tế (**Quyết định 1246/QĐ-BYT** và **Thông tư 30/2012/TT-BYT**).

---

## 🚀 Hướng Dẫn Khởi Chạy

### Cách 1: Chạy nhanh bằng 1-Click trên Windows
Nhấp đúp chuột vào file **`run_web.bat`**. 
Trình duyệt web sẽ tự động mở tại địa chỉ: **`http://localhost:8000`**.

### Cách 2: Khởi chạy bằng Terminal / Dòng lệnh
1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
2. Khởi chạy ứng dụng:
   ```bash
   python -m uvicorn app:app --host 127.0.0.1 --port 8000
   ```
3. Mở trình duyệt truy cập: `http://localhost:8000`.

---

## 🌟 Các Tính Năng Đầy Đủ

1. **📊 Tổng quan (Dashboard)**: Theo dõi tổng suất ăn trong ngày, tổng số món ăn, tiến độ kiểm thực và tình trạng 24 tiêu chí an toàn của Bộ Y Tế.
2. **📅 Lập Thực đơn tuần**: Lập thực đơn 7 ngày từ Thứ 2 đến Chủ nhật, tìm kiếm nhanh từ 250+ món ăn, cấu hình số suất ăn các ca Trưa, Chiều, Tối và Món nước.
3. **🛒 Dự trù nguyên vật liệu**: Tự động tính toán lượng CẦN theo số suất ăn & định mức, dải dung sai cho phép [Min, Max] (±5%). Nhập Thực Nhận có đèn báo xanh/đỏ tức thì.
4. **📋 Mẫu 1: Kiểm thực Bước 1 (Trước chế biến)**: Kiểm tra nguồn gốc, hạn dùng, chứng từ và cảm quan nguyên liệu tươi sống & khô. Tự động điền nhà cung cấp, địa chỉ, SĐT, người giao.
5. **🍳 Mẫu 2: Kiểm thực Bước 2 (Khi chế biến)**: Kiểm tra điều kiện vệ sinh, thời gian nấu chín. **Cảnh báo an toàn 2 giờ**: tự động báo động đỏ nếu nấu xong quá 2 giờ trước giờ ăn theo đúng quy chuẩn Bộ Y Tế.
6. **🍽️ Mẫu 3: Kiểm thực Bước 3 (Trước khi ăn)**: Kiểm tra trước khi ăn, thời gian chia món ăn xong, thời gian bắt đầu ăn, dụng cụ che đậy inox, cảm quan.
7. **🏷️ Mẫu 4: In Nhãn Lưu Mẫu**: Thiết kế tem dán hũ inox đẹp mắt, chuẩn kích thước. Hỗ trợ lọc in theo ca hoặc in trọn bộ tem dán trong ngày.
8. **🧊 Mẫu 5: Sổ Lưu & Hủy Mẫu**: Theo dõi tủ lạnh lưu mẫu (2°C - 8°C). Tự động nhận diện 100g (món đặc) hoặc 150ml (món lỏng). **Tự động cộng đúng 24 giờ để ra thời gian hủy mẫu**.
9. **🛡️ Kiểm Tra An Toàn (24 Tiêu Chí)**: Rà soát tự động 24 tiêu chí quy chuẩn QĐ 1246/QĐ-BYT với trạng thái OK, Cảnh báo và chỉ dẫn cách khắc phục cụ thể.
10. **⚙️ Cài đặt & Danh mục**: Quản lý thông tin công ty, cơ sở, nhân sự; thêm/sửa/xóa danh mục 250+ món ăn, nhà cung cấp, định mức gram/suất.
11. **🖨️ In ấn & Xuất Excel**: In trực tiếp các biểu mẫu theo chuẩn khổ giấy A4 hoặc bấm "Xuất Excel" để tải file `.xlsx`.