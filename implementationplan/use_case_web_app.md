# Biểu đồ Use Case - Giao diện Web App Thực thụ (Bitcoin Wallet & Node)

Để xây dựng một Web App thực thụ (không còn bị gò bó vào kịch bản Demo tĩnh), hệ thống sẽ được thiết kế mô phỏng một **Ví tiền điện tử (Wallet)** kết hợp với **Bảng điều khiển Máy chủ (Node Dashboard)**. 

Dưới đây là mô hình Tác nhân (Actors) và Kịch bản sử dụng (Use Cases) theo đúng tiêu chuẩn thực tế:

---

## 1. Phân tích Tác nhân (Actors)

1. **User (Người dùng Ví):** Bất kỳ người nào sử dụng ứng dụng Web như một chiếc ví cá nhân. Họ không cần quan tâm đến máy chủ, chỉ quan tâm đến việc quản lý tài sản, nhận/gửi tiền và bảo mật khóa.
2. **Miner (Thợ đào / Quản trị Node):** Là người vận hành máy chủ Node Bitcoin. **Miner kế thừa toàn bộ các chức năng của một User** (vì Miner cũng cần có ví để giao dịch và lưu trữ), nhưng được bổ sung thêm các quyền hạn hệ thống để can thiệp vào mạng lưới (đóng block, thu phí).

---

## 2. Kịch bản Sử dụng (Use Cases)

### A. Nhóm chức năng của Người dùng (User)

**1. Quản lý Tài khoản & Bảo mật (Key & Address Management)**
*   **Tạo/Lưu trữ Khóa:** Tự động khởi tạo và lưu trữ an toàn Private Key / Public Key cục bộ.
*   **Tạo Địa chỉ ví:** Sinh ra các định dạng địa chỉ khác nhau (Legacy, Nested Segwit, Native Segwit, Taproot) tùy theo nhu cầu sử dụng để đưa cho đối tác.

**2. Giao diện Phân tích (Dashboard & Ledger)**
*   **Xem Bảng điều khiển (Dashboard):** Xem biểu đồ thống kê tài sản, tỷ lệ biến động.
*   **Xem Số dư:** Quét mạng lưới để tính toán tổng UTXO khả dụng trong ví.
*   **Xem Sổ cái Giao dịch (Ledger/History):** Tra cứu lịch sử các giao dịch gửi/nhận đã thực hiện (Kèm theo TXID, thời gian, số xác nhận).

**3. Tương tác Tài chính (Transactions)**
*   **Giao dịch Chuyển/Nhận tiền:** Nhập địa chỉ người nhận, số lượng BTC, và tùy chỉnh phí thợ đào (Fee Rate). 
*   **Đọc/Gửi Tin nhắn (OP_RETURN):** Đính kèm tin nhắn văn bản vào giao dịch (Ghi vĩnh viễn lên Blockchain) hoặc đọc tin nhắn từ người khác gửi đến.
*   **Phát sóng (Broadcast):** Hệ thống tự động gom UTXO, Ký tên bằng Private Key và đẩy giao dịch lên mạng lưới (Mempool).

---

### B. Nhóm chức năng của Thợ Đào (Miner)

*(Miner sở hữu toàn bộ các Use Case của User ở trên, cộng thêm các Use Case đặc quyền hệ thống dưới đây)*

**1. Quản lý Mạng lưới & Khai thác (Network & Mining)**
*   **Gom Giao dịch:** Quét Mempool để gom các giao dịch đang chờ (của các User khác) vào một Block mới. 
*   **Đóng Block (Mine Block):** Kích hoạt lệnh giải thuật toán để tạo ra Block mới trên mạng lưới (Ở môi trường Regtest là lệnh `generatetoaddress`).

**2. Quản lý Thu nhập (Revenue Management)**
*   **Nhận Phần thưởng Block (Block Reward):** Nhận tự động phần thưởng hệ thống cấp (ví dụ 12.5 BTC / 6.25 BTC) khi đóng Block thành công.
*   **Thu Phí Giao dịch (Collect TX Fees):** Ăn trọn phần tiền chênh lệch (Tiền thừa) do các User gán vào giao dịch để trả công.
