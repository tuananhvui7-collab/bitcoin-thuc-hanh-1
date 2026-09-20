# Giải Thích Logic Lõi (Core Logic) 

Tài liệu này giải thích chi tiết cách bộ mã nguồn (đặc biệt là `tx_builder.py` và `app.py`) đáp ứng trọn vẹn 9 bước theo yêu cầu của "Simplified Flow" (Đề bài thực hành).

---

## Bước 1: Khởi tạo mạng Regtest và Đào Block
**Yêu cầu:** Cài đặt Bitcoin mạng cục bộ (Regtest) và đào block bằng `generatetoaddress`.
**Giải pháp:** 
- Toàn bộ mạng lưới được giả lập thông qua Docker (`docker-compose.yml`), khởi chạy image `bitcoin/bitcoin:28.0` với cờ `-regtest=1`.
- Chức năng đào block được tích hợp thẳng vào nút **"Miner: Đóng Block"** trên Web. Khi bấm, Backend gọi RPC `generatetoaddress(1, miner_address)`.

## Bước 2: Suy ra 4 loại địa chỉ từ 1 Private Key
**Yêu cầu:** Từ 1 Private Key, tạo ra Legacy (P2PKH), Nested Segwit (P2SH), Native Segwit (P2WPKH), và Taproot (P2TR).
**Giải pháp:** 
Trong `tx_builder.py`, hàm `derive_all_address_types(wif_string)` sử dụng thư viện `python-bitcoin-utils` để lấy Public Key, sau đó gọi các hàm tương ứng:
- `pub_key.get_address().to_string()` (Legacy)
- `pub_key.get_segwit_address().to_string()` (Native Segwit)
- `pub_key.get_nested_segwit_address().to_string()` (Nested Segwit)
- `pub_key.get_taproot_address().to_string()` (Taproot)

## Bước 3: Nạp Coin cho địa chỉ (Faucet from miner)
**Yêu cầu:** Lấy phần thưởng đào block để làm vốn.
**Giải pháp:**
- Ví "Alice" (Ví test 1) được hardcode trong biến môi trường `.env` dưới quyền `MINER_WIF`.
- Mỗi lần đào block (Bước 1), phần thưởng 50 BTC (hoặc thấp hơn tùy Halving) sẽ chảy thẳng vào địa chỉ của Alice. Alice dùng tiền này chuyển cho các địa chỉ khác.

## Bước 4: Liệt kê UTXO của từng địa chỉ
**Yêu cầu:** Lấy danh sách UTXO của một địa chỉ.
**Giải pháp:** 
Hàm `get_utxos_by_address(address)` dùng lệnh RPC `scantxoutset` để quét nhanh toàn bộ UTXO trên Blockchain mà không cần đánh index toàn bộ ví. 

## Bước 5: Coin Selection (Chọn UTXO tối ưu)
**Yêu cầu:** Chọn tổ hợp UTXO đủ để gửi, giảm thiểu rác và phí.
**Giải pháp:** 
Hàm `select_utxos(utxos, target_amount)` trong `tx_builder.py` thực hiện sắp xếp mảng UTXO theo giá trị giảm dần (Lớn đến Nhỏ). Thuật toán sẽ ưu tiên lấy các tờ tiền mệnh giá lớn nhất để nhét vào giao dịch, qua đó làm giảm số lượng Input (Bytes), trực tiếp giảm Phí Thợ Đào.

## Bước 6: Ký từng UTXO (Phân biệt ECDSA và Schnorr)
**Yêu cầu:** Legacy/Segwit ký bằng ECDSA, Taproot ký bằng Schnorr.
**Giải pháp:** 
Đây là trái tim của hàm `build_and_sign_tx`. Vòng lặp duyệt qua từng Input:
- Nếu Input là `legacy` hoặc `segwit` (Native/Nested): Gọi `priv_key.sign_input(...)` (Thuật toán ECDSA).
- Nếu Input là `taproot`: Phải truyền toàn bộ mảng Script và Amount của TẤT CẢ inputs vào hàm `priv_key.sign_taproot_input(...)` (Thuật toán Schnorr).

## Bước 7: Build Raw Transaction Hex
**Yêu cầu:** Gộp các thành phần lại thành chuỗi Hex.
**Giải pháp:** 
Cuối hàm `build_and_sign_tx`, đối tượng `Transaction` được khởi tạo với mảng Inputs (đã ký) và mảng Outputs (địa chỉ nhận + địa chỉ tiền thừa). Sau đó gọi `tx.serialize()` để chuyển hóa toàn bộ object thành chuỗi Hex.

## Bước 8: Broadcast lên mạng
**Yêu cầu:** Phát sóng giao dịch qua `sendrawtransaction`.
**Giải pháp:** 
Tại `app.py`, sau khi nhận được mã Hex từ `tx_builder`, Backend lập tức gọi `proxy.sendrawtransaction(hex_tx)` để bắn dữ liệu vào Mempool của Node. Nếu thành công, Node sẽ trả về TXID.

## Bước 9: Giao diện UI/UX
**Yêu cầu:** Có giao diện trực quan thay vì chỉ dùng Command Line.
**Giải pháp:** 
Dự án được bọc trong một Web App viết bằng Flask (Backend) và Bootstrap 5 (Frontend). Đã có cơ chế bảo vệ Trải nghiệm người dùng thông qua Memory Cache (`LOCKED_UTXOS`), lịch sử Sổ cái (`history.json`) và thông báo lỗi rõ ràng.
