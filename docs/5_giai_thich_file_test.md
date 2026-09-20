# Hướng dẫn Kiểm thử (Test & Tools)

Mặc dù Bài thực hành này không yêu cầu viết Unit Test phức tạp (như `pytest`), chúng ta vẫn có các phương thức và công cụ kiểm thử cốt lõi để đảm bảo hệ thống hoạt động đúng.

## 1. Web App chính là môi trường Test toàn diện nhất
Khác với các đoạn code Python chay trên Console, Giao diện Web được thiết kế để bao phủ (cover) toàn bộ các trường hợp sử dụng (Use Case) và lỗi (Edge Case).
- **Test kết nối Node:** Khi tải trang, Web App tự động gọi hàm RPC. Nếu Node tắt, giao diện tự bắt lỗi và hiển thị cảnh báo đỏ rực.
- **Test logic chọn UTXO (Coin Selection) & Double-Spend:** Khi người dùng gửi tiền, Web App tự động gọi vào `tx_builder`. Cơ chế `LOCKED_UTXOS` đảm bảo 1 đồng tiền không bị đem ra ký 2 lần.

## 2. File `generate_key.py` (Công cụ hỗ trợ Sinh Khóa)
Trong quá trình test, việc phải lấy 1 Private Key mới toanh để nhận tiền là vô cùng cần thiết.
Thay vì mò mẫm thư viện, bạn có thể chạy:
```bash
python generate_key.py
```
**Chức năng:**
- Khởi tạo thư viện `bitcoinutils` với cấu hình môi trường Regtest.
- Gọi hàm `PrivateKey()` để lấy ra một chuỗi ngẫu nhiên chuẩn toán học.
- Xuất ra chuỗi WIF (Wallet Import Format). Bạn có thể bôi đen copy và dán vào nút "Tạo Ví Mới" hoặc "Dùng WIF khác" trên UI.

## 3. Cách Test "Vòng Đời Giao Dịch" (End-to-End)
Để test từ A-Z xem hệ thống của mình có xịn hay không, bạn hãy thực hiện kịch bản sau:
1. Đăng nhập bằng Ví Test 1 (Alice).
2. Lấy WIF của Alice (từ file `.env`), hoặc dùng `generate_key.py` tạo 1 ví Bob mới.
3. Chuyển tiền từ Alice sang Bob với Phí = `0.0001 BTC`.
4. Quan sát Sổ cái: Báo trạng thái **Mempool** (Đang chờ). Số dư Alice bị trừ ngay lập tức.
5. Nhấn **Miner: Đóng Block**.
6. Sổ cái nhảy sang **Confirmed**, số dư Bob tăng lên. 
👉 Nếu mọi thứ mượt mà, bài toán Logic Cốt lõi của bạn đạt điểm 10/10.
