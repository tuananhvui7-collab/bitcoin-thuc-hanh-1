# Thiết kế Ứng dụng Ví Bitcoin (Regtest)

Tài liệu này tổng hợp toàn bộ các sơ đồ phân tích thiết kế hệ thống của Web App, bao gồm Use Case (Trường hợp sử dụng), Activity (Hoạt động) và Sequence (Trình tự).

## 1. Usecase Diagram
**Tác nhân (Actors):**
1. **Người dùng (User)**: Bất kỳ ai sở hữu Private Key (WIF).
2. **Thợ đào (Miner)**: Đóng vai trò xác nhận giao dịch trên mạng lưới.

**Các Usecase chính:**
- Đăng nhập bằng Private Key (WIF).
- Xem bảng điều khiển (Số dư tổng, số dư từng loại địa chỉ).
- Gửi tiền (Chỉ định số tiền và phí thợ đào).
- Xem lịch sử giao dịch (Sổ cái).
- Đóng Block (Dành cho Thợ đào).

## 2. Activity Diagram (Sơ đồ hoạt động)

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[Đăng nhập bằng WIF]
    B --> C{Xác thực WIF?}
    C -- Lỗi --> B
    C -- Thành công --> D[Tải thông tin Ví]
    
    D --> E[Hiển thị Dashboard: Số dư & Địa chỉ]
    E --> F[Người dùng nhập lệnh Chuyển tiền]
    
    F --> G[Nhập: Địa chỉ nhận, Số lượng BTC, Phí thợ đào BTC]
    G --> H{Kiểm tra tính hợp lệ?}
    H -- Không hợp lệ --> F
    
    H -- Hợp lệ --> I[Tạo Transaction Gốc qua tx_builder]
    I --> J[Gom UTXO chưa bị khóa]
    J --> K[Ký Giao Dịch bằng WIF]
    K --> L[Broadcast lên Node Bitcoin]
    
    L --> M[Khóa các UTXO vừa tiêu vào Mempool Lock]
    M --> N[Ghi vào Sổ cái trạng thái: Đang chờ]
    
    N --> O{Thợ đào đóng Block?}
    O -- Chưa --> N
    O -- Rồi --> P[Mở khóa UTXO & Cập nhật Sổ cái: Hoàn thành]
    
    P --> Q([Kết thúc])
```

## 3. Sequence Diagram (Sơ đồ tuần tự)

```mermaid
sequenceDiagram
    autonumber
    actor U as Người Dùng
    participant W as Web App (Frontend)
    participant B as Backend (Flask API)
    participant C as Core Logic (tx_builder)
    participant N as Bitcoin Node (Regtest)
    actor M as Thợ Đào (Miner)

    U->>W: Nhập Private Key (WIF)
    W->>B: GET /api/wallet/info?wif=...
    B->>C: Lấy danh sách Địa chỉ & UTXO
    C->>N: listunspent (qua RPC)
    N-->>C: Trả về UTXOs
    C-->>B: Tổng số dư & Các địa chỉ
    B-->>W: Dữ liệu Dashboard JSON
    W-->>U: Hiển thị Giao diện Ví

    U->>W: Nhập lệnh Chuyển tiền (Địa chỉ, Số BTC, Phí)
    W->>B: POST /api/transfer (Data)
    B->>C: build_and_sign_tx()
    C->>C: Tính toán thuật toán Coin Selection
    C->>C: Ký giao dịch (ECDSA / Schnorr)
    C->>N: sendrawtransaction (qua RPC)
    N-->>C: txid (Giao dịch nằm ở Mempool)
    C-->>B: txid & danh sách UTXO đã dùng
    B->>B: Đưa UTXO vào danh sách Khóa (LOCKED_UTXOS)
    B-->>W: Thông báo Thành công
    W-->>U: Cập nhật Sổ cái (Trạng thái: Mempool)

    M->>W: Bấm nút "Đóng Block"
    W->>B: POST /api/mine
    B->>N: generatetoaddress (qua RPC)
    N-->>B: Hash của Block mới & Phần thưởng
    B->>B: Xóa danh sách Khóa (LOCKED_UTXOS)
    B->>B: Cập nhật Sổ cái (Trạng thái: Confirmed)
    B-->>W: Kết quả Khai thác
    W-->>M: Báo cáo Thưởng Thợ đào
```
