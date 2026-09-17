# Sơ đồ Tuần tự (Sequence Diagram)

Sơ đồ này mô tả chi tiết cách 3 thành phần hệ thống giao tiếp với nhau theo thời gian thực (Time-based):
1. **Frontend (Giao diện Web HTML/JS)**: Nơi User và Miner tương tác.
2. **Backend (Flask API)**: Bộ não điều khiển, nơi chứa File `tx_builder.py`.
3. **Bitcoin Node (Regtest)**: Máy chủ cốt lõi xử lý chuỗi khối.

---

## 1. Kịch bản Gửi tiền và Đóng Block hoàn chỉnh

```mermaid
sequenceDiagram
    autonumber
    actor User as Giao diện Web (User/Miner)
    participant Flask as Flask Backend (tx_builder)
    participant Node as Bitcoin Regtest Node

    %% PHA 1: KHỞI TẠO GIAO DỊCH
    Note over User,Node: PHA 1: CHUYỂN TIỀN VÀO MEMPOOL
    
    User->>Flask: POST /api/send_tx (Address, Amount, Fee)
    activate Flask
    
    Flask->>Flask: Kiểm tra Lock (Chống Double Spend)
    Flask->>Node: Lệnh lấy UTXO (get_unspents)
    Node-->>Flask: Trả về danh sách UTXOs
    
    Flask->>Flask: select_utxos() & Tính phí động
    Flask->>Flask: Khóa các UTXO (Locked In-memory)
    Flask->>Flask: Ký tên (sign_transaction_inputs)
    
    Flask->>Node: Lệnh phát sóng (sendrawtransaction)
    Node-->>Flask: Trả về mã TXID
    
    Flask-->>User: Hiển thị thành công (Giao dịch đang ở Mempool)
    deactivate Flask

    %% PHA 2: ĐÓNG BLOCK
    Note over User,Node: PHA 2: THỢ ĐÀO CHỐT BLOCK
    
    User->>Flask: POST /api/mine_block (Số lượng block=1)
    activate Flask
    
    Flask->>Node: Lệnh đào (generatetoaddress)
    Node-->>Flask: Trả về Block Hash mới
    
    Flask->>Flask: Xóa trạng thái Khóa (Unlock UTXOs)
    
    Flask-->>User: Thông báo: Block đã được tạo!
    deactivate Flask

    %% PHA 3: CẬP NHẬT GIAO DIỆN
    Note over User,Node: PHA 3: CẬP NHẬT DỮ LIỆU THỜI GIAN THỰC
    
    User->>Flask: GET /api/dashboard_info
    activate Flask
    
    Flask->>Node: Truy vấn số dư Alice, Bob, Miner
    Node-->>Flask: Dữ liệu số dư mới (Đã cộng trừ tiền và phí)
    
    Flask-->>User: Gửi JSON dữ liệu số dư
    deactivate Flask
    
    User->>User: Rerender lại Giao diện, Số tiền nhảy lên.
```
