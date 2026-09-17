# Sơ đồ Hoạt động (Activity Diagrams)

Tài liệu này sử dụng Mermaid flowchart để mô phỏng chính xác đường đi nước bước (Luồng xử lý) của hệ thống khi người dùng thao tác trên Web App.

## 1. Luồng Hoạt động: Chuyển tiền (Send Transaction)

Đây là luồng hoạt động khi Người dùng (User) bấm nút Gửi tiền trên Web.

```mermaid
flowchart TD
    %% Tác nhân Người dùng
    Start([Bắt đầu]) --> FillForm[User điền Thông tin: Địa chỉ nhận, Số tiền, Phí]
    FillForm --> ClickSend[Bấm nút 'Phát Sóng']
    
    %% Xử lý Backend
    ClickSend --> CheckLock{UTXO có bị kẹt?}
    
    CheckLock -- Có --> ErrorLock[Báo lỗi: Đang có giao dịch chờ, xin thử lại sau] --> End([Kết thúc])
    CheckLock -- Không --> ScanUTXO[Quét ví lấy danh sách UTXO]
    
    ScanUTXO --> CheckBalance{Đủ tiền không?}
    CheckBalance -- Không đủ --> ErrorBalance[Báo lỗi: Số dư không đủ] --> End
    
    CheckBalance -- Đủ --> LockUTXO[Khóa tạm thời các UTXO vừa chọn]
    LockUTXO --> BuildTx[Tạo Khung Giao dịch thô]
    BuildTx --> SignTx[Ký tên bằng Private Key]
    
    %% Tương tác Node
    SignTx --> Broadcast[Gọi lệnh sendrawtransaction đẩy lên Node]
    Broadcast --> CheckBroadcast{Node chấp nhận?}
    
    CheckBroadcast -- Bị từ chối --> UnlockError[Gỡ Khóa UTXO] --> ErrorNode[Báo lỗi từ Node] --> End
    CheckBroadcast -- Thành công --> ReturnTXID[Trả về TXID cho giao diện]
    ReturnTXID --> ShowWait[Hiển thị trạng thái: Chờ đưa vào Block]
    ShowWait --> End
```

## 2. Luồng Hoạt động: Đóng Block (Mine Block)

Đây là luồng hoạt động khi Thợ Đào (Miner) bấm nút Đóng Block trên bảng điều khiển.

```mermaid
flowchart TD
    StartMine([Bắt đầu]) --> ClickMine[Miner bấm nút 'Đóng 1 Block']
    
    ClickMine --> CallMine[Backend gọi lệnh 'generatetoaddress']
    CallMine --> ReceiveHash[Nhận được Hash của Block mới]
    
    ReceiveHash --> UnlockAll[Backend gỡ khóa toàn bộ UTXO bị kẹt]
    UnlockAll --> ParseBlock[Phân tích Block vừa đào để tính phí thu được]
    
    ParseBlock --> UpdateUI[Cập nhật lại toàn bộ Bảng điều khiển Số dư]
    UpdateUI --> EndMine([Kết thúc])
```
