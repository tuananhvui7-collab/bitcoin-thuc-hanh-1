# Cấu trúc Dữ liệu & JSON trong Ứng dụng

Tài liệu này giải phẫu toàn bộ các biến `[]` (List/Mảng) và `{}` (Dictionary/JSON Object) được sử dụng trong mã nguồn (`app.py`, `tx_builder.py`) để bạn dễ hình dung dòng chảy của dữ liệu.

---

## 1. Cấu trúc của một UTXO (`u`)
Khi gọi hàm `get_utxos_by_address()` (trò chuyện với Node Bitcoin), Node sẽ trả về một mảng chứa các đồng tiền chưa tiêu (UTXO). Khi bạn thấy code viết `for u in data['unspents']:`, thì biến `u` chính là một cục JSON trông như thế này:

```json
{
  "txid": "f8a7c2b3d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6",
  "vout": 0,
  "amount": 50.00000000,
  "scriptPubKey": "76a914892c...88ac",
  "desc": "pkh([d34db33f/0'/0'/0']...)",
  "confirmations": 101,
  "addr_type": "legacy" // Trường này do app tự gắn thêm vào ở tx_builder.py
}
```
**Giải thích:**
- `txid`: Mã ID của Giao dịch sinh ra tờ tiền này.
- `vout`: Vị trí của tờ tiền trong giao dịch (Index).
- `amount`: Mệnh giá tờ tiền (tính bằng BTC).
- Cặp `txid` + `vout` chính là "Số seri" độc nhất của tờ tiền, dùng để đưa vào biến `LOCKED_UTXOS` chống Double-Spend.

---

## 2. Cấu trúc Sổ cái `TRANSACTION_HISTORY`
Biến `TRANSACTION_HISTORY = []` lưu một danh sách (Mảng) các giao dịch do Web App tạo ra. Mỗi giao dịch bên trong mảng này là một Object `{}`:

```json
[
  {
    "txid": "3b29c9...a1b2",
    "amount": "1.50000000",
    "fee": "0.00001000",
    "recipient": "bcrt1qxyza...v98k",
    "status": "Mempool",
    "time": "2026-09-18 18:30:45"
  },
  {
    "txid": "9a8b7c...d6e5",
    "amount": "10.00000000",
    "fee": "0.00005000",
    "recipient": "bcrt1qmnop...q32j",
    "status": "Confirmed",
    "time": "2026-09-18 18:15:10"
  }
]
```
**Giải thích:**
- `status`: Bắt đầu luôn là `"Mempool"` (Chờ xác nhận). Khi bấm "Đóng Block", App sẽ quét và sửa toàn bộ chữ `"Mempool"` thành `"Confirmed"`.

---

## 3. Cấu trúc API Trả về (Từ Flask Backend gửi cho Javascript Frontend)

### A. API `/api/wallet/info`
Khi bạn đăng nhập hoặc tải lại trang, Javascript sẽ gọi API này để lấy toàn bộ thông tin hiển thị lên Giao diện.

```json
{
  "success": true,
  "data": {
    "total_balance": "55.50000000",
    "addresses": {
      "legacy": "mwybXW2Kx2yJqwJjZpCxyW2f5t7a1c",
      "nested_segwit": "2MwzD1x2yJqwJjZpCxyW2f5t7a1c",
      "native_segwit": "bcrt1qwzD1x2yJqwJjZpCxyW2f5t7a1c",
      "taproot": "bcrt1pwzD1x2yJqwJjZpCxyW2f5t7a1c"
    }
  },
  "history": [
    // Bê nguyên mảng TRANSACTION_HISTORY nhét vào đây
  ]
}
```

### B. API `/api/transfer` (Nhận vào và Trả ra)

**Gói tin Javascript (Frontend) GỬI LÊN Backend (POST Request):**
```json
{
  "sender_wif": "cTzexFWsvcXqx5TNuB3iNBx9T7xn6HXTZ5eASPL5Xdsb7sAoSXwC",
  "recipient_address": "bcrt1qxyza...v98k",
  "amount": "1.5",
  "absolute_fee": "0.00001"
}
```

**Gói tin Backend TRẢ VỀ sau khi chuyển tiền thành công:**
```json
{
  "success": true,
  "txid": "3b29c9...a1b2",
  "fee_paid": "0.00001",
  "message": "Giao dịch đã đẩy lên Mempool!"
}
```

---

> [!TIP]
> **Ký hiệu trong Python:**
> - `[]` (List): Tương đương Array trong Javascript. Dùng để chứa nhiều cục dữ liệu giống nhau (ví dụ: Danh sách các tờ tiền, danh sách lịch sử giao dịch).
> - `{}` (Dictionary): Tương đương JSON Object. Dùng để biểu diễn 1 thực thể có nhiều thuộc tính (ví dụ: 1 tờ tiền UTXO cụ thể, 1 Giao dịch cụ thể).
> - Khác biệt lớn nhất: Để lấy giá trị trong Python, ta viết `u['txid']` (Dùng ngoặc vuông bọc chuỗi), còn trong Javascript thì ta có thể viết tắt là `u.txid` (Dùng dấu chấm).
