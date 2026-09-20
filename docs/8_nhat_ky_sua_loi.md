# Nhật Ký Sửa Lỗi (Troubleshooting & Bug Fixes)

Trong quá trình phát triển Ứng dụng Ví Bitcoin Regtest, chúng ta đã gặp phải một số vấn đề kỹ thuật thú vị. Dưới đây là danh sách các lỗi và cách khắc phục để đảm bảo ứng dụng hoạt động mượt mà và trực quan nhất.

## 1. Lỗi Không Parse được Địa chỉ Nested Segwit & Taproot

**Vấn đề:** 
Khi người dùng copy địa chỉ Nested Segwit hoặc Taproot và dán vào ô "Địa chỉ người nhận", bấm "Khởi tạo Giao dịch" thì API trả về lỗi 400 (Bad Request).

**Nguyên nhân:** 
Trong hàm `build_transaction` (file `app.py`), backend chỉ cố gắng ép kiểu chuỗi địa chỉ đó về `P2wpkhAddress` (Native Segwit) hoặc `P2pkhAddress` (Legacy). Khi gặp địa chỉ Nested Segwit (`P2shAddress`) hoặc Taproot (`P2trAddress`), thư viện `python-bitcoin-utils` văng lỗi `Exception` vì sai định dạng.

**Cách khắc phục:**
Cập nhật khối `try-except` để parse lần lượt cả 4 loại địa chỉ. Nếu loại này lỗi thì catch và nhảy sang parse loại khác, cho đến khi tìm được đúng class để lấy ra `ScriptPubKey` hợp lệ.

## 2. Thắc Mắc: Ký ECDSA cho 10 tờ UTXO nhưng Legacy chỉ có 70 BTC?

**Vấn đề (Mặt giao diện/Người dùng hiểu lầm):** 
Người dùng gửi 100 BTC. Hệ thống chọn 10 tờ UTXO (mỗi tờ 10 BTC). Trên UI, toàn bộ 10 tờ này đều hiện chữ ký là **ECDSA**. Người dùng thắc mắc: "Ví Legacy của tôi chỉ có 70 BTC (tức 7 tờ), làm sao có thể ký ECDSA cho cả 10 tờ?"

**Nguyên nhân (Logic cốt lõi của Bitcoin):** 
Nhiều người nghĩ rằng chỉ có địa chỉ Legacy mới dùng thuật toán ECDSA. Thực tế:
- **Legacy (P2PKH):** Dùng ECDSA.
- **Nested Segwit (P2SH) & Native Segwit (P2WPKH):** Cũng dùng ECDSA! (Chỉ khác cách nhét chữ ký vào Script/Witness).
- **Taproot (P2TR):** Dùng SCHNORR.

Khi gom 100 BTC, thuật toán Coin Selection lấy 7 tờ từ Legacy và 3 tờ từ Native Segwit. Vì cả 2 loại địa chỉ này đều dùng ECDSA, nên UI hiện chữ ký là ECDSA cho cả 10 tờ là **hoàn toàn chính xác**.

**Cách khắc phục:**
Để tránh hiểu lầm, UI đã được cập nhật. Trên mỗi tờ UTXO được chọn ở Bước 2, hệ thống sẽ in rõ tên loại địa chỉ gốc bên cạnh thuật toán ký (Ví dụ: `Legacy - ECDSA`, `Native Segwit - ECDSA`).

## 3. Lỗi Hiển thị Số dư Gộp (Không tách biệt từng địa chỉ)

**Vấn đề:** 
Hàm `get_total_balance` chỉ cộng dồn tổng số tiền của 4 loại địa chỉ thành 1 con số `total_balance` duy nhất, khiến người dùng không biết mỗi loại địa chỉ (Legacy, Taproot...) đang nắm giữ bao nhiêu UTXO/BTC.

**Cách khắc phục:**
- Backend: Cập nhật hàm quét UTXO để khởi tạo 1 dictionary `balances`. Ứng với mỗi vòng lặp `addr_type`, lưu riêng số dư của địa chỉ đó vào `balances[addr_type]`.
- Frontend: Bổ sung các thẻ `<span>` nhỏ nằm cạnh địa chỉ trong Box "Ví Của Tôi" để render chi tiết số dư cho từng chuẩn địa chỉ.

## 4. Bổ sung Tính năng Xem Chi Tiết Giao Dịch (Sổ cái)

**Vấn đề:** 
Lịch sử giao dịch (`history.json`) chỉ lưu các thông tin bề nổi (số tiền, phí, thời gian). Người dùng muốn xem chi tiết Input/Output của một giao dịch cụ thể khi click vào TXID.

**Cách khắc phục:**
Tạo thêm endpoint `GET /api/transaction/<txid>`. API này sẽ gọi thẳng vào Node Bitcoin thông qua lệnh `proxy.getrawtransaction(txid, True)`. Lệnh này có cờ `True` giúp Node tự động decode chuỗi Raw Hex thành file JSON chi tiết (chứa mảng `vin`, `vout`, khối lượng byte...). Từ đó, Frontend dùng Bootstrap Modal để parse và hiển thị thông tin chuyên sâu này.
