# Sổ tay Xử lý Lỗi (Troubleshooting & Bugs)

Trong quá trình dev dự án này, hệ thống có thể sẽ gặp vài "ổ gà" kinh điển. Đây là cách xử lý:

## 1. Lỗi: Giao diện web hiển thị `0.0000` và toàn bộ địa chỉ là `...`
- **Nguyên nhân:** Web App không thể kết nối tới Node Bitcoin qua cổng RPC (18443).
- **Hiện tượng:** Nếu bật Console trên Trình duyệt, sẽ thấy lỗi 500. Backend báo `[WinError 10061] No connection could be made`.
- **Cách khắc phục:** 
  1. Kiểm tra xem Docker đã chạy chưa bằng lệnh `docker-compose ps`.
  2. Bật lại Node bằng lệnh `docker-compose up -d bitcoind`.
  3. F5 lại trình duyệt, Toast thông báo màu đỏ sẽ biến mất và số dư sẽ tải lại bình thường.

## 2. Lỗi: Gửi tiền báo lỗi `Fee rate (X) is lower than minimum fee rate (Y)`
- **Nguyên nhân:** Mạng lưới Bitcoin luôn có cấu hình Phí Tối Thiểu (Minimum Relay Fee / Fallback Fee). Nếu bạn nhập phí ở UI nhỏ hơn con số này, Node sẽ sút giao dịch của bạn ra.
- **Cách khắc phục:** 
  1. Nếu chạy Node thủ công, nhớ thêm cờ `-fallbackfee=0.0002` vào lúc khởi động.
  2. Tránh nhập số `0.00000001` BTC (quá thấp). Hãy nhập từ `0.00001` BTC trở lên.

## 3. Lỗi: Ví không có đồng nào (Báo lỗi ValueError)
- **Nguyên nhân:** WIF bạn đang dùng chưa từng được nạp tiền, hoặc bạn chưa đào Block (Miner) lần nào kể từ lúc bật Regtest.
- **Cách khắc phục:** Đăng nhập vào ví Alice (Ví test 1), copy địa chỉ của ví mới, và dùng ví Alice gửi một ít BTC qua. Cuối cùng, nhấn "Đóng Block" để chốt đơn!

## 4. Lỗi: Double-Spend / "Mempool conflict" từ Backend
- **Nguyên nhân:** Mạng bị kẹt, hoặc bạn đã xóa file `history.json` và khởi động lại Backend, dẫn tới việc biến `LOCKED_UTXOS` (bảo vệ in-memory) bị clear trắng. Sau đó bạn lại cố gửi thêm 1 giao dịch sử dụng đồng tiền đang bị kẹt ở Mempool.
- **Cách khắc phục:** Đơn giản nhất là Bấm nút **"Miner: Đóng Block"** để Node xác nhận toàn bộ lệnh cũ, đưa mọi thứ về vạch xuất phát.

## 5. Lỗi: Node Bitcoin trong Docker không tìm thấy thư mục Data
- **Nguyên nhân:** Windows không chia sẻ quyền truy cập (File Sharing) cho Docker.
- **Cách khắc phục:** Mở Docker Desktop -> Settings -> Resources -> File Sharing và Add đường dẫn thư mục chứa Code dự án vào.
