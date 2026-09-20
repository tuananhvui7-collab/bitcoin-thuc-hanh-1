# Tổng hợp Lệnh CLI Cấu hình hệ thống

Tài liệu này giải thích các lệnh Command Line (CLI) dùng để thiết lập, quản lý và kiểm tra dự án.

## 1. Môi trường Python (Nền tảng ảo)
```bash
# Tạo môi trường ảo (Virtual Environment) để cài thư viện mà không rác máy tính
python -m venv venv

# Kích hoạt môi trường ảo (Windows)
venv\Scripts\activate

# Cài đặt toàn bộ thư viện cần thiết cho dự án
pip install -r requirements.txt
```

## 2. Các lệnh khởi chạy Dự án Thủ công (Dành cho Dev)
Nếu bạn không dùng Docker, đây là cách chạy Node và App bằng tay:

```bash
# Chạy Máy chủ Flask Backend
python src/app.py
```
*(Lưu ý: Bạn phải thiết lập biến môi trường `RPC_HOST=127.0.0.1` trong `.env` nếu chạy thủ công).*

## 3. Quản lý Node bằng Docker Compose (Dành cho Giai đoạn 3)
```bash
# Bật hệ thống (chạy ngầm)
docker-compose up -d

# Tắt hệ thống
docker-compose down

# Kiểm tra trạng thái các service
docker-compose ps

# Xem log thời gian thực của Node Bitcoin
docker-compose logs -f bitcoind
```

## 4. Tương tác với Bitcoin Node (Bitcoin-cli)
Nếu bạn muốn tự tay chọc vào Node qua CLI thay vì qua Web App:

```bash
# Lấy thông tin mạng lưới
bitcoin-cli -regtest -rpcuser=dev -rpcpassword=devpass getnetworkinfo

# Đào 1 block gửi vào địa chỉ chỉ định
bitcoin-cli -regtest -rpcuser=dev -rpcpassword=devpass generatetoaddress 1 "bcrt1q..."

# Xem dữ liệu thô của một giao dịch
bitcoin-cli -regtest -rpcuser=dev -rpcpassword=devpass getrawtransaction "txid" true
```
