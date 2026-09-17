# Tài liệu Giải thích File `tx_builder.py` (Phiên bản nâng cấp Mix UTXO)

Sau khi được phê duyệt bỏ qua phần thực hành tự gõ code do thời lượng quá tải, tôi đã tự động nâng cấp toàn bộ file `tx_builder.py`. Việc nâng cấp này phá vỡ giới hạn "mỗi lần chuyển tiền chỉ dùng 1 loại ví", biến phần mềm thành một cái ví thực thụ: "Gom tất cả tiền trong túi vào một rổ, tờ nào cũng được, miễn đủ tiền là ký".

Dưới đây là giải thích bóc tách từng dòng logic:

---

## 1. Hàm `build_and_sign_tx`: Khởi tạo và Bốc UTXO

*   `sender_addresses = derive_all_address_types(sender_wif)`: Đầu tiên, từ 1 cái Private Key (WIF), ta sinh ra 4 địa chỉ tương ứng.
*   `all_utxos = []`: Tạo một cái rổ trống.
*   `for addr_type, addr_string in sender_addresses.items():` Chạy vòng lặp qua 4 địa chỉ.
*   `u["addr_type"] = addr_type`: **ĐÂY LÀ ĐIỂM CHỐT.** Mỗi khi tìm thấy một tờ tiền (UTXO), ta không chỉ lấy số tiền, mà lấy cây bút dạ viết lên tờ tiền đó nhãn hiệu của ví (`legacy`, `taproot`...). Điều này là bắt buộc, vì lát nữa khi qua khâu Ký Tên, thuật toán phải nhìn vào nhãn này để biết dùng bút ký kiểu ECDSA hay Schnorr.
*   `selected_utxos_draft, _ = select_utxos(all_utxos, target_amount)`: Bốc nháp để tính thử xem cần bao nhiêu tờ tiền (để từ đó quy ra dung lượng Bytes).
*   `change_script = sender_pub.get_segwit_address().to_script_pub_key()`: Chốt thiết kế: Dù lấy tiền từ bất kỳ đâu, tiền thừa (Change) luôn được gửi về địa chỉ **Native Segwit** của bản thân người gửi. (Bởi vì Native Segwit phí giao dịch rẻ nhất, giúp tối ưu chi phí cho lần gửi sau).

---

## 2. Hàm `sign_transaction_inputs`: Thuật toán Ký đa năng

Đây là tinh hoa của kỹ thuật mã hóa (Cryptography). Mỗi loại tờ tiền đòi một thuật toán ký riêng biệt:

*   `all_scripts` và `all_amounts`: Thuật toán Taproot (Schnorr signature) cực kỳ khắc nghiệt. Nó không cho phép ký lẻ tẻ từng tờ. Nó bắt bạn phải đưa cho nó danh sách Số lượng và Mã khóa của TOÀN BỘ các tờ tiền nằm trong giao dịch đó cùng một lúc. Do đó ta phải duyệt vòng lặp `for utxo in selected_utxos` để gom 2 cái list này lại trước.
*   `if a_type == "legacy"`: Tờ tiền cổ đại. Dùng hàm `priv_key.sign_input`. Chữ ký được đẩy thẳng vào `script_sig` (Một vùng dữ liệu cồng kềnh, làm tốn phí).
*   `elif a_type == "native_segwit"`: Tờ tiền hiện đại. Dùng hàm `priv_key.sign_segwit_input`. Chữ ký KHÔNG ném vào `script_sig` nữa, mà nhét vào một cái "Túi phụ" gọi là `witnesses` (Vùng dữ liệu này được tính phí rẻ hơn 4 lần).
*   `elif a_type == "taproot"`: Tờ tiền tối tân nhất. Dùng hàm `priv_key.sign_taproot_input` truyền vào 2 cái mảng đã chuẩn bị ở trên. Chữ ký (nhẹ hơn, bảo mật hơn) cũng được ném vào `witnesses`.

Bạn có thể tự tin chạy thử file `test_signer.py` để xem mọi thứ đã được gom thành 1 luồng mượt mà như thế nào.
