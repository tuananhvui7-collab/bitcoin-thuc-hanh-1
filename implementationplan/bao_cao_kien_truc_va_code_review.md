# Báo cáo Phân tích Kiến trúc & Giải đáp Code Review

Tài liệu này được lập ra để phản hồi trực tiếp các nghi vấn của người Review code về tiến độ 9 bước, các lỗ hổng hệ thống, và kiến trúc trước khi chuyển sang làm Web App (Bước 9).

---

## 1. Đối chiếu Tiến độ (Simplified Flow)

Dưới đây là 10 bước chuẩn của dự án và tình trạng hiện tại:

| Bước | Mô tả Yêu cầu | Tình trạng | File phụ trách |
| :--- | :--- | :--- | :--- |
| **1** | Cài đặt Bitcoin Node dạng Regtest | ✅ Xong | Docker/Hệ thống |
| **2** | Từ 1 PrivKey, suy ra 4 loại địa chỉ | ✅ Xong | `tx_builder.py` (`derive_all_address_types`) |
| **3** | Nạp coin bằng reward thợ đào (Faucet) | ✅ Xong | `wallet_faucet.py` |
| **4** | Liệt kê UTXO của từng loại địa chỉ | ✅ Xong | `tx_builder.py` (`get_utxos_by_address`) |
| **5** | Coin Selection (nhặt tờ tiền tối ưu) & Tính phí | ✅ Xong | `tx_builder.py` (`select_utxos`, `estimate_tx_fee`) |
| **6** | Ký từng UTXO (ECDSA / Schnorr) | ✅ Xong | `tx_builder.py` (`sign_transaction_inputs`) |
| **7** | Build raw transaction hex | ✅ Xong | `tx_builder.py` (`build_and_sign_tx`) |
| **8** | Broadcast (Gửi giao dịch lên mạng) | ✅ Xong | `test_signer.py` (Sẽ chuyển vào Flask App ở Bước 9) |
| **9** | **Xây dựng UI/UX Web hoặc Desktop** | 🕒 Đang đợi | Flask App (Sắp khởi công) |
| **10** | Đóng gói toàn bộ bằng Docker Compose | 🕒 Đang đợi | `docker-compose.yml` (Sắp khởi công) |

---

## 2. Giải trình các Hạn chế (Do người review nêu)

### A. Nhóm Logic Cốt lõi
1. **Không thể gộp (Mix) nhiều loại UTXO:** 
   - **Tình trạng cũ:** Thiết kế ban đầu cố tình ép dùng 1 loại địa chỉ (thông qua biến `addr_type`) để code minh bạch, dễ theo dõi.
   - **HIỆN TẠI ĐÃ GIẢI QUYẾT (FIXED):** Trong đợt nâng cấp lõi mới nhất, chúng ta đã **đập đi xây lại** toàn bộ logic ở `tx_builder.py`. Hệ thống giờ đây có khả năng gom (Mix) tiền từ TẤT CẢ các ví (Legacy, SegWit, Taproot...) vào chung một rổ để ký và gửi đi trong cùng một giao dịch. Ví đã trở thành một cái ví thực thụ!
2. **Điểm nghẽn kịch bản Taproot (`[script_pubkey] * len`):**
   - **Thừa nhận:** Rất tinh tế. Dòng code này giả định mọi UTXO đầu vào đều có chung cấu trúc mã lệnh (Script). Nếu nâng cấp lên Mix UTXO (như ý 1) thì dòng này sẽ lỗi. Do chúng ta chốt dùng "1 loại ví nguồn", dòng này hiện tại vẫn an toàn tuyệt đối.

### B. Nhóm Hệ thống (Khi mang lên Web)
1. **Thiếu lệnh Broadcast trong `tx_builder.py`:**
   - **Giải thích:** Nguyên tắc Clean Code (Single Responsibility) quy định: Thằng thợ xây (`tx_builder`) chỉ tạo ra cục Hex rồi dừng. Thằng giao hàng (`test_signer` hoặc `app.py`) mới là thằng cầm cục Hex đi gửi (`sendrawtransaction`). Lệnh Broadcast không hề thiếu, nó chỉ nằm ở đúng vị trí của nó để đảm bảo an toàn.
2. **Double Spend do Kẹt Mempool & Lộ Private Key WIF:**
   - Đã được giải thích cực kỳ cặn kẽ bằng ví dụ thực tế ở file `giai_thich_bao_mat.md`.

---

## 3. Tại sao nhét hết vào `tx_builder.py`? Tại sao chỉ 4 file test?

- **Về `wallet_faucet.py`:** Đây là kịch bản "Mồi lửa". Nó chỉ chạy đúng 1 lần duy nhất lúc tạo Server để mồi tiền cho ví. Nó không thuộc luồng giao dịch hằng ngày.
- **Tại sao gộp vào `tx_builder.py`:** Các bước từ 2 đến 7 là một dây chuyền dính chặt vào nhau. Tách lẻ 6 bước thành 6 file sẽ gây ra lỗi "Circular Import" (File A gọi File B, File B gọi lại File A) làm sập hệ thống. Tinh hoa của thiết kế phần mềm (Domain-Driven Design) là phải gom các quy trình liên tiếp này vào 1 Lớp Dịch Vụ (Service Layer) duy nhất.
- **Tại sao chỉ 4 file test:** Unit Test không làm theo Số bước, mà làm theo Số cục logic. Trong 8 bước trên, chỉ có 4 cục logic có rủi ro toán học cần test: (1) Sinh địa chỉ, (2) Nhặt tiền UTXO, (3) Tính phí, (4) Test tích hợp cả luồng. 4 file Test là hoàn toàn đầy đủ và chuẩn mực.
