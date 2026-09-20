# Báo cáo Phân tích Logic Web App (Flask Backend & Frontend JS)

Sau khi hệ thống Lõi đã hoàn thiện (hỗ trợ Mix UTXO an toàn), chúng ta tiến hành xây dựng một Web App thực thụ. Quá trình này hoàn toàn tuân theo nguyên lý thiết kế ứng dụng web hiện đại (Client-Server Architecture) và sử dụng Bootstrap 5 Dark Theme cực kỳ hiện đại.

Dưới đây là phần bóc tách giải thích cặn kẽ từng file, từng dòng code.

---

## 1. Bảo mật với Biến môi trường (`.env`)

Thay vì vứt mã PIN (Private Key) thẳng vào code (Hardcode), chúng ta sử dụng file `.env`.
```env
ALICE_WIF=cSmKSQgPLqn9jSt89KjbhTiBpT7qK4jWrdQnmgMzHPuhZvVbp82V
BOB_WIF=cUi51ejxfidY9JMwFg8orA1zFFhHCwyGtsKcb42gaTPRScGrVNGJ
MINER_WIF=cW5zfDLu6USbGVfCpYeeLoE7YTVTbejSj92G4iugka5nYXSvp6M5
```
- **Lý do**: Đây là một nguyên tắc bảo mật cơ bản. Bất kỳ ai nhìn vào mã nguồn (`app.py`) cũng sẽ không biết được Private Key của người dùng. Khi chạy trên Docker, các biến này sẽ được truyền vào từ bên ngoài an toàn.
- File `.env.example` được tạo ra để công khai (làm mẫu cho dev khác xem cấu trúc biến), còn file `.env` sẽ bị ẩn đi.

---

## 2. Máy chủ Backend (`src/app.py`)

Đây là trung tâm điều phối mọi hoạt động. Nó kết nối Giao diện người dùng với bộ Core `tx_builder.py` bên dưới.

### A. Quản lý trạng thái UTXO cục bộ (Mempool UTXO Locking)
```python
LOCKED_UTXOS = set()
```
- **Bản chất vấn đề**: Khi bạn vừa nhấn nút gửi tiền, Giao dịch (Transaction) được đẩy vào Mempool chờ Thợ Đào xác nhận. Tuy nhiên, API của Node Bitcoin đôi khi vẫn trả về các đồng tiền (UTXO) đó là "chưa bị tiêu" cho đến khi Block được đóng. Nếu không có cơ chế lọc, thuật toán `tx_builder` sẽ bốc LẠI chính những đồng tiền đó cho giao dịch tiếp theo -> Giao dịch thứ 2 sẽ bị Node từ chối vì lỗi Double Spend.
- **Cách giải quyết (UX)**: Tạo một biến toàn cục (Memory Cache) tên là `LOCKED_UTXOS`. Mỗi khi gửi tiền thành công, Web App "đánh dấu khóa" các tờ tiền vừa dùng. Khi người dùng bấm gửi tiếp, thuật toán tính số dư sẽ tự động VỨT BỎ (lọc) các đồng tiền đang bị khóa này ra khỏi giỏ hàng. Đây là kỹ thuật đảm bảo trải nghiệm người dùng mượt mà, tránh việc Web App gửi lệnh lỗi lên Node.

### B. Hàm quét Số dư (`get_total_balance`)
```python
def get_total_balance(wif: str) -> Decimal:
    addresses = derive_all_address_types(wif)
    total = Decimal('0')
    
    for addr_type, addr in addresses.items():
        data = get_utxos_by_address(addr)
        unspents = data.get('unspents', [])
        for u in unspents:
            utxo_id = f"{u['txid']}:{u['vout']}"
            if utxo_id not in LOCKED_UTXOS:
                total += Decimal(str(u['amount']))
    return total
```
- Dòng `for addr_type, addr in addresses.items()`: Quét toàn bộ 4 loại ví (Legacy, Segwit, Taproot) của người dùng.
- Dòng `if utxo_id not in LOCKED_UTXOS`: Loại bỏ những đồng tiền đang "nằm chờ" ở Mempool, chỉ cộng những đồng thực sự Khả Dụng (Available Balance).

### C. Giao thức chuyển tiền (`/api/transfer`)
```python
# Gọi API Lõi để build giao dịch
signed_tx, dynamic_fee, selected_utxos = build_and_sign_tx(...)

# Khóa (Lock) các UTXO đã dùng để tránh Double Spend liên tục trên UI
for u in selected_utxos:
    utxo_id = f"{u['txid']}:{u['vout']}"
    LOCKED_UTXOS.add(utxo_id)
```
- Bất cứ khi nào gọi hàm lõi thành công, ta duyệt qua danh sách `selected_utxos` (các đồng tiền bị lấy ra) và tống chúng vào bộ nhớ đệm `LOCKED_UTXOS`.

### D. Thợ Đào làm việc (`/api/mine`)
```python
# Đào 1 Block
proxy.generatetoaddress(1, miner_addr)

# Xóa toàn bộ Locked UTXOs
LOCKED_UTXOS.clear()
```
- Khi Thợ Đào nhấn nút "Đóng Block", Node sẽ tóm toàn bộ Giao dịch trong Mempool để đưa lên Chuỗi.
- Lúc này, những đồng tiền đang bị "treo" đã chính thức biến mất khỏi hệ thống. Do đó, ta chỉ cần gọi `LOCKED_UTXOS.clear()` để làm sạch bộ đệm khóa, trả lại luồng gửi tiền mượt mà cho lần tiếp theo.

---

## 3. Giao diện Web Client (HTML + JS)

### A. Theme Siêu "Ngầu" (Bootstrap 5 Dark Mode)
- Ở thẻ HTML, ta thêm `data-bs-theme="dark"` để website tự động kích hoạt chế độ Tối (Dark mode). Phối hợp với viền màu sáng (Xanh, Đỏ, Vàng) tạo cảm giác như một ứng dụng giao dịch tài chính (Trading Dashboard).
- Biểu tượng lấy từ `bootstrap-icons`.

### B. JavaScript Bất Đồng Bộ (`main.js`)
- Việc lấy số dư và cập nhật UI được thực hiện bằng Ajax (`fetch`), hoàn toàn chạy ngầm (Asynchronous), người dùng không bao giờ cần bấm F5 để Load lại trang.
- **Auto-polling**: `setInterval(fetchBalances, 5000);` cứ 5 giây một lần hệ thống tự gọi API lấy số dư mới nhất. 
- **Chống chớp nháy (Flicker)**: `if (aliceBal.innerText !== data.alice) aliceBal.innerText = data.alice;` chỉ thay đổi DOM nếu số tiền thực sự thay đổi, tránh tình trạng giật màn hình khi Data trả về giống hệt cũ.
- Khi người dùng nhấn Nút Gửi hoặc Nút Đào Block, nút bấm đó sẽ bị làm mờ (Disable) và hiện cái Vòng Xoay (Loading Spinner) bằng lệnh `btnTransfer.innerHTML = '<span class="spinner-border...>'`. Điều này tránh việc người dùng nhấp đúp (Double click) tạo ra 2 lệnh chuyển tiền cùng một lúc. Khi API trả về xong, nút bấm lại trở về bình thường trong khối `finally { ... }`.
