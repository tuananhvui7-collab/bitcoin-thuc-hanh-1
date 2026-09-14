# 📖 BÁO CÁO CHI TIẾT CODE BITCOIN (Cửu Âm Chân Kinh)

Tài liệu này được biên soạn đặc biệt để giúp bạn hiểu rõ **TẠI SAO** chúng ta lại viết code như vậy, thay vì chỉ biết **CÁCH** copy-paste. Hãy đọc nó một cách thư giãn, coi nó như một cuốn truyện.

---

## PHẦN 1: TỔNG QUAN KIẾN TRÚC THƯ MỤC
Dự án của chúng ta đã được quy hoạch lại rất rõ ràng:
```
bitcoin-thuc-hanh-1/
├── src/                  <-- Trái tim của dự án (Chứa logic chính)
│   ├── wallet_faucet.py  <-- Khởi tạo ví, thiết lập kết nối ban đầu
│   └── tx_builder.py     <-- Xưởng lắp ráp Giao dịch (Sinh địa chỉ, Ký tên, Quét UTXO)
├── tests/                <-- Khu vực kiểm thử
│   └── test_signer.py    <-- Nơi gọi các hàm ở src/ ra để chạy thử nghiệm 4 loại địa chỉ
```
**Luật bất thành văn:** File ở `tests/` dùng để chạy thử. File ở `src/` không tự chạy, nó chỉ chứa công cụ để chỗ khác gọi ra xài.

---

## PHẦN 2: SO SÁNH CÁC MẠNG BITCOIN (MAINNET vs TESTNET vs REGTEST)

Trước khi đi sâu vào code, bạn cần phân biệt 3 thế giới của Bitcoin:

| Đặc điểm | Mainnet (Mạng chính) | Testnet (Mạng thử nghiệm) | Regtest (Mạng tự sướng) |
| :--- | :--- | :--- | :--- |
| **Bản chất** | Sân chơi thật, tiền thật. | Sân chơi thử, giống thật 99%. | Sân chơi riêng tư trên máy tính của bạn. |
| **Giá trị đồng coin** | 1 BTC = $60,000 | 1 tBTC = $0 | 1 rBTC = $0 |
| **Thợ đào (Miner)** | Hàng triệu máy đào toàn cầu. | Cộng đồng dev toàn cầu đào. | Chỉ có duy nhất 1 mình bạn tự đào tự xài. |
| **Thời gian ra Block** | 10 phút/Block | 10 phút/Block | Trả về NGAY LẬP TỨC (Khi bạn gõ lệnh `generatetoaddress`). |
| **Xin tiền (Faucet)** | Phải mua bằng tiền thật. | Xin trên web (Rất khó vì web hay chết). | Tự gọi lệnh đào Block là có 50 BTC xài tẹt ga. |

> [!NOTE] 
> Bài thực hành này chúng ta dùng **Regtest** vì nó không phụ thuộc vào internet, không mất thời gian chờ 10 phút để xác nhận, và chúng ta là "Chúa tể" có thể tự in ra bao nhiêu tiền tùy thích để test code.

---

## PHẦN 3: GIẢI MÃ CÁC FILE LÕI TRONG `SRC/`

### 1. File `wallet_faucet.py`
**Mục đích:** Cài đặt "cơ sở hạ tầng" ban đầu. Nó tạo ra cái ví cho Node (để Node có chỗ cất tiền) và móc nối Python với Node.
- **`setup('regtest')`**: Báo cho thư viện biết "Tôi đang chơi mạng Regtest nhé, đừng tạo địa chỉ Mainnet".
- **`proxy.createwallet("devwallet")`**: Tạo một cái ví rỗng trên Node.
- **`proxy.generatetoaddress(101, ...)`**: Lệnh đào 101 Blocks. (Tại sao lại là 101? Vì Bitcoin quy định tiền đào được phải bị giam đủ 100 blocks mới được tiêu. Đào 101 blocks để block đầu tiên được giải phóng).

### 2. File `tx_builder.py`
Đây là "Nhà máy" của chúng ta. Nó chứa các hàm công cụ:

#### A. Hàm `derive_all_address_types(wif)`
- **Input:** Chuỗi `WIF` (Ví dụ: `cSmKS...` - Chìa khóa riêng tư).
- **Hoạt động:** Từ 1 cái chìa khóa duy nhất, nó tạo ra 4 ổ khóa (4 loại địa chỉ):
  1. `legacy`: Bắt đầu bằng chữ `m` hoặc `n`. Cũ nhất, phí đắt nhất.
  2. `nested_segwit`: Bắt đầu bằng số `2`. Cải tiến hơn một chút.
  3. `native_segwit`: Bắt đầu bằng `bcrt1q`. Nhẹ, phí rẻ.
  4. `taproot`: Bắt đầu bằng `bcrt1p`. Mới nhất (2021), siêu bảo mật, siêu nhẹ, phí rẻ nhất.
- **Output:** Một Dictionary chứa cả 4 địa chỉ.

#### B. Hàm `get_utxos_by_address(address)` và `select_utxos(...)`
- **Khái niệm UTXO (Unspent Transaction Output):** Bitcoin không có khái niệm "Số dư tài khoản" (Số dư = 100). Nó chỉ có những "Tờ tiền lẻ". Nếu bạn có 3 tờ 10 BTC, 20 BTC, 70 BTC, tổng tài sản của bạn là 100 BTC. 3 tờ tiền đó gọi là 3 UTXO.
- **`get_utxos_by_address`**: Quét xem bạn đang cầm trong tay những tờ tiền lẻ (UTXO) nào.
- **`select_utxos`**: Hàm này bốc các tờ tiền cho đủ số bạn muốn gửi. **Logic cực hay ở chỗ:** Nó sắp xếp các tờ tiền từ lớn đến bé (`reverse=True`). 
  - *Lý do:* Nếu bạn cần gửi 10 BTC, thay vì bốc 100 tờ 0.1 BTC (làm Giao dịch nặng chịch -> phí siêu đắt), nó sẽ ưu tiên bốc 1 tờ 50 BTC. Phần thừa 40 BTC sẽ được trả lại (gọi là Tiền thối - Change).

#### C. Hàm `sign_transaction_inputs(...)`
- Đây là cốt lõi của **Bước 6**. Tiền (UTXO) là một cái két sắt khóa bằng Ổ khóa (Public Key). Để tiêu tiền, bạn phải lấy Khóa bí mật (Private Key) để **Ký tên** (Mở khóa).
- **Legacy:** Ký bằng ECDSA, để thẳng chữ ký vào `script_sig` (Ngay mặt tiền của giao dịch -> Cồng kềnh).
- **Segwit:** Ký bằng ECDSA, nhưng ném chữ ký ra đằng sau vào một chỗ gọi là `witness` (Phụ lục -> Giảm nhẹ kích thước).
- **Taproot:** Ký bằng **Schnorr** thay vì ECDSA. Ký siêu nhanh, dung lượng siêu nhỏ.

#### D. Hàm `estimate_tx_fee(...)`
- **Tại sao phải có hàm này?** Phí Bitcoin không cố định! Nó tính bằng dung lượng (`bytes`).
- `Phí = Dung lượng × Giá cước`. Hàm này đếm xem bạn dùng mấy tờ tiền (Input) và trả lại mấy tờ tiền (Output) để nhân với các hệ số như `148 bytes` (Legacy) hay `57.5 bytes` (Taproot) rồi tính ra số BTC bạn phải trả cho Thợ đào.

---

## PHẦN 4: GIẢI MÃ BÀI TEST `tests/test_signer.py`
Quy trình thực thi chuẩn (Từ Bước 1 đến 8) gói gọn trong file này. Mạch truyện của nó như sau:

1. **Khởi động:** Nạp chìa khóa `WIF` của Alice và Bob.
2. **Kẻ thứ 3 xuất hiện:** Tạo ra tài khoản của `Thợ Đào` để hứng tiền phí.
3. **Vòng lặp 4 loại địa chỉ:** Nó chạy 4 lần cho 4 loại địa chỉ để chứng minh thuật toán nhà máy của chúng ta hoàn hảo với mọi chuẩn Bitcoin.
4. **Bốc nháp (Đoán phí):** Gọi `select_utxos` lấy tạm tiền để đếm số lượng tờ tiền, lấy số lượng đó vứt vào hàm `estimate_tx_fee` để tính ra **Phí Động (Dynamic Fee)**.
5. **Bốc thật (Tính cả tiền gửi + Phí):** Lấy tờ 50 BTC, cắt ra làm 3 phần:
   - Phần 1 (Output 1): Trả Bob 10 BTC.
   - Phần 2 (Tàng hình): Vứt ra đường `0.0000x` BTC làm phí.
   - Phần 3 (Output 2): Cầm về tiền thối `39.999x` BTC.
6. **Đóng dấu mộc:** Gọi hàm Ký của nhà máy.
7. **Phát sóng (Bước 8):** Ném file Hex lên mạng (`proxy.sendrawtransaction`). Lúc này tiền vẫn kẹt ở Hàng chờ (Mempool).
8. **Thợ Đào Chốt Đơn (Kết thúc chu trình):** Ép Node đào ngay 1 Block (`generatetoaddress(1)`). Lúc này, Thợ Đào gom giao dịch của Alice lại, đóng vào Block 326 (Ví dụ), và Thợ Đào hốt luôn cái phần tiền phí tàng hình kia vào túi mình!

---
*Tài liệu này là "phao cứu sinh" để bạn ôn tập lại toàn bộ kiến thức. Chúc bạn bảo vệ đồ án thành công rực rỡ!*
