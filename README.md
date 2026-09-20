# 🚀 Bài Thực Hành 1: Mô Phỏng Mạng Lưới Bitcoin (Regtest) & Ví Non-Custodial

Dự án này là một Web App hoàn chỉnh mô phỏng lại cách mạng lưới Bitcoin hoạt động dưới góc nhìn của một chiếc Ví phi tập trung (Non-custodial Wallet), giao tiếp trực tiếp với Bitcoin Node cục bộ (Mạng Regtest).

## 🗂 Cấu trúc Tài liệu Dự Án (Docs)

Để hiểu sâu về cách hoạt động của dự án, vui lòng đọc các tài liệu kỹ thuật trong thư mục `docs/` theo thứ tự sau:

1. [docs/1_thiet_ke_app.md](docs/1_thiet_ke_app.md) - Xem Sơ đồ Usecase, Sequence, Activity để hiểu luồng ứng dụng.
2. [docs/2_giai_thich_logic_loi.md](docs/2_giai_thich_logic_loi.md) - Cách code lõi Python giải quyết 9 bước của bài toán cốt lõi.
3. [docs/3_data_structures.md](docs/3_data_structures.md) - Giải phẫu JSON và cấu trúc dữ liệu của các UTXO.
4. [docs/4_cli_commands.md](docs/4_cli_commands.md) - Danh sách các lệnh Command Line cần biết.
5. [docs/5_giai_thich_file_test.md](docs/5_giai_thich_file_test.md) - Cách tạo thêm Private Key và chiến lược Test.
6. [docs/6_docker_guide.md](docs/6_docker_guide.md) - Bí kíp đóng gói dự án lên bất kỳ máy nào bằng Docker.
7. [docs/7_troubleshooting_bugs.md](docs/7_troubleshooting_bugs.md) - Cẩm nang sửa 5 lỗi phổ biến nhất khi chạy app.

---

## 🛠 Hướng Dẫn Sử Dụng (Quick Start)

### Yêu Cầu Cài Đặt
- Cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- (Chỉ khi không dùng Docker) Python 3.10+ và Bitcoin Core.

### Chạy Dự Án bằng 1 Lệnh (Bằng Docker)

Mở Terminal (Command Prompt) tại thư mục chứa dự án và chạy:
```bash
docker-compose up -d --build
```

Đợi 15-30 giây để hệ thống tải Node và thiết lập môi trường. Sau đó:
👉 **Mở Trình duyệt và truy cập: [http://localhost:5000](http://localhost:5000)**

---

## 🎮 Cách Trải Nghiệm Ứng Dụng (End-to-End Test)

1. **Đăng nhập:** 
   - Trên thanh Menu, chọn **Ví Test 1 (Alice)** để lấy Ví Cổ Đông (Ví này sẽ luôn nhận được 50 BTC mỗi khi đào Block).
   - *Mẹo:* Bạn có thể gõ `python generate_key.py` ở Terminal để tự tạo một ví hoàn toàn mới, sau đó chọn **"Dùng WIF Khác"** để đăng nhập bằng mã vừa tạo.
2. **Chuyển tiền:**
   - Tại màn hình Dashboard, copy một địa chỉ (VD: Native Segwit) của ví khác.
   - Kéo xuống Form chuyển tiền, Dán địa chỉ nhận vào.
   - Nhập số BTC muốn gửi và **Nhập Phí Thợ Đào (BTC)**. (Ví dụ: `0.0001` BTC).
   - Bấm **Chuyển tiền**.
3. **Quan sát Mempool (Sổ Cái):**
   - Bạn sẽ thấy giao dịch vừa tạo lọt vào bảng Sổ Cái với trạng thái màu vàng **"Đang chờ (Mempool)"**.
   - Lúc này, số dư của bạn đã bị giảm (App tự khóa UTXO để tránh Double-Spend). Tuy nhiên, người nhận vẫn chưa có tiền.
4. **Khai thác Block (Mining):**
   - Bấm nút **"Miner: Đóng Block"** (Nút màu vàng trên cùng góc phải).
   - Thợ Đào (Alice) sẽ nhận được Tiền thưởng 50 BTC gốc + Tiền phí `0.0001` BTC mà bạn vừa trả.
   - Sổ Cái sẽ tự động cập nhật trạng thái giao dịch thành **"Hoàn thành"** màu xanh.
5. **Chúc mừng!** Bạn vừa thực hiện trọn vẹn vòng đời của một giao dịch Bitcoin!
