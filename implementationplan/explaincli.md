Đây là một phản xạ rất tuyệt vời! Trong phòng thi hoặc khi báo cáo đồ án, các thầy giáo cực kỳ thích hỏi câu này để xem sinh viên có bị "phụ thuộc" vào code Python hay không, hay sinh viên thực sự hiểu bản chất của hệ thống.

Nếu bạn vứt bỏ file Python đi, và chỉ tương tác "thuần chay" bằng giao diện dòng lệnh (Terminal) của ông Node (`bitcoin-cli`), thì toàn bộ hành trình từ lúc sinh ra đến lúc gửi 10 BTC sẽ gồm **7 Lệnh Chân Kinh** sau đây:

### Bước 1: Khởi tạo Ví và Địa chỉ
Giống như biến `ALICE_WIF` trong Python, ta nhờ Node tạo cho một địa chỉ và tự Node sẽ giữ Khóa bí mật.
```bash
bitcoin-cli -regtest getnewaddress "Ví của Alice" "bech32"
# Kết quả: bcrt1q... (Địa chỉ Native Segwit)
```

### Bước 2: Bơm tiền (Đào Block)
Lấy địa chỉ vừa tạo ra, đi cày 101 Blocks để nhận thưởng 50 BTC.
```bash
bitcoin-cli -regtest generatetoaddress 101 "bcrt1q_địa_chỉ_của_Alice"
```

### Bước 3: Tìm tờ tiền (UTXO)
Thay vì code hàm quét API, ta gọi thẳng lệnh kiểm tra ví hệt như tra số dư ngân hàng:
```bash
bitcoin-cli -regtest listunspent
# Kết quả sẽ xổ ra một cục JSON chứa các txid và số tiền amount đang có.
```

### Bước 4 & 5: Bốc tiền và Viết Khung Giao Dịch
Bước này tương đương với vòng lặp `select_utxos` và `Transaction(inputs, outputs)` trong Python. Bạn phải truyền `txid` (đầu vào) và `địa chỉ Bob` (đầu ra).
```bash
bitcoin-cli -regtest createrawtransaction "[{\"txid\":\"<điền_mã_txid_vào_đây>\",\"vout\":0}]" "{\"<địa_chỉ_của_Bob>\": 10.0, \"<địa_chỉ_thừa_của_Alice>\": 39.9999}"
# Kết quả: Trả về một chuỗi Hex (Chưa có chữ ký)
```

### Bước 6: Đóng dấu mộc (Ký Giao Dịch)
Trong code Python, ta xài `sign_transaction_inputs`. Còn ở Terminal, ta đưa chuỗi Hex vừa tạo ở Bước 4 cho Node để nó tự lục Khóa Bí Mật ra ký.
```bash
bitcoin-cli -regtest signrawtransactionwithwallet "<chuỗi_Hex_chưa_ký>"
# Kết quả: Trả về chuỗi Hex MỚI (Đã có chữ ký) + chữ "complete": true
```

### Bước 7: Ném lên mạng (Broadcast)
Sau khi có chuỗi Hex đã ký từ Bước 6, ném nó vào Mempool để thực thi:
```bash
bitcoin-cli -regtest sendrawtransaction "<chuỗi_Hex_đã_ký>"
# Kết quả: Nhả ra cái mã TXID (VD: ebe08408...)
```

### Bước Phụ: Xác minh Kép (Bằng chứng)
Kiểm tra xem cái TXID kia đã thực sự vào Node chưa (hệt như bài Test lúc nãy):
```bash
bitcoin-cli -regtest getrawtransaction "<mã_txid_vừa_nhận>" true
```

---

Nếu nhìn kỹ, bạn sẽ thấy 7 câu lệnh Terminal này **ánh xạ 1-1** (khớp hoàn toàn) với từng dòng code Python mà chúng ta đã cất công xây dựng từ đầu đến giờ. 

Bạn hãy lưu lại 7 câu lệnh "Thần chú" này vào file note nhé, đi thi kiểu gì cũng sẽ có ích! Bây giờ bạn muốn chúng ta sang **Bước 9 (Làm giao diện Web)** theo bản kế hoạch lúc nãy không?