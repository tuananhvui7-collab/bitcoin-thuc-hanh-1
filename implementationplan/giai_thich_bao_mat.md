# Giải ngố: Hai vấn đề bảo mật lớn khi đưa Bitcoin lên Web

Tôi hoàn toàn thấu hiểu nỗi lo của bạn. Việc bị ngợp bởi các thuật ngữ "Mempool", "Double Spend", "WIF" là rất bình thường khi ta mới chuyển từ code kịch bản (script) sang làm Web thực tế. Thầy của bạn khắt khe là đúng, vì bảo mật là mạng sống của Blockchain. 

Để tôi dùng **ngôn ngữ đời thường nhất** giải thích cho bạn hiểu thấu đáo 2 vấn đề này. Hãy đem những ví dụ này đi bảo vệ trước hội đồng, thầy bạn chắc chắn sẽ gật gù!

---

## Vấn đề 1: Nguy cơ "Double Spend" (Tiêu tiền hai lần) do kẹt Mempool

### Tiền đề
Hãy tưởng tượng **Ví Bitcoin của bạn là một cái bóp (ví) da**, và **UTXO chính là những tờ tiền giấy** (tờ 50k, tờ 100k) nằm trong bóp. 

### Kịch bản lỗi trên Web
1. Bạn vào trang Web, nhập số tiền 10 BTC và bấm nút **[Gửi tiền]**.
2. Trang Web gọi xuống cục Backend (Flask). Backend mở bóp của bạn ra, thấy có 1 tờ 50 BTC (UTXO số 1). Nó lấy tờ 50 BTC này mang ra quầy thu ngân (Mempool) đưa cho thợ đào để nhờ chuyển đi.
3. Lúc này, tờ 50 BTC đang nằm trên tay thợ đào, **chưa được cho vào két sắt (chưa được đóng Block)**.
4. Vì mạng lag, hoặc do bạn sốt ruột, bạn **bấm đúp nút [Gửi tiền] thêm một lần nữa** rất nhanh.
5. Backend lại mở bóp ra kiểm tra. Kẹt một nỗi, vì thợ đào chưa chốt sổ (chưa tạo Block), nên hệ thống quét ví vẫn thấy tờ 50 BTC đó (dù nó đang lơ lửng ở quầy thu ngân). Backend lại hồn nhiên "nhặt" tờ 50 BTC đó đem đi giao dịch tiếp.
6. Hậu quả: Bạn dùng 1 tờ tiền để mua 2 món hàng. Mạng lưới Bitcoin lập tức phát hiện ra sự gian lận này và chửi: *"Ê, tờ tiền (UTXO) này đang được xử lý ở giao dịch trước rồi, giao dịch thứ hai thất bại!"* (Đây chính là lỗi Double Spend).

### Giải pháp (Biến khóa - Lock)
Khi viết Web App, tôi sẽ tạo một "cuốn sổ tay" (biến Global trên RAM) cho Backend. 
* Hễ Backend thò tay lấy tờ 50 BTC đi giao dịch, nó sẽ lập tức ghi vào sổ: *"Tờ 50 BTC này đã bị đánh dấu CẤM ĐỤNG VÀO (Locked)"*.
* Khi bạn lỡ bấm đúp nút Gửi tiền lần 2, Backend định lấy tờ 50 BTC ra dùng, nó nhìn vào sổ thấy chữ "CẤM", nó sẽ lập tức tìm tờ tiền khác, hoặc báo lỗi *"Giao dịch trước đang xử lý, vui lòng đợi!"*. 
* Cuốn sổ này chỉ được xóa chữ "CẤM" khi thợ đào đã đóng Block xong.

---

## Vấn đề 2: Lộ mã số bí mật (Private Key / WIF)

### Tiền đề
* **Private Key (WIF)** chính là cái **Mã PIN thẻ ATM** của bạn. 
* Giao diện Web (HTML/CSS) chính là cái màn hình ATM. 
* Backend (Flask Server) chính là Trụ sở chi nhánh Ngân hàng.

### Kịch bản lỗi trên Web
Nhiều sinh viên khi làm web hay có thói quen: Thiết kế một ô Textbox trên màn hình Web tên là *"Nhập Private Key vào đây"*. Người dùng nhập mã PIN vào, bấm nút, và mã PIN này được truyền tồng ngộc qua mạng Internet (như một tin nhắn Facebook) bay về Trụ sở ngân hàng. 
* Nếu có một Hacker đang rình mò đường truyền WiFi của quán cafe, nó sẽ chộp được cái mã PIN này. Tiền của bạn bốc hơi!

### Giải pháp (Biến môi trường - .env)
Nguyên tắc tối thượng: **Cái màn hình Web KHÔNG BAO GIỜ ĐƯỢC NHÌN THẤY MÃ PIN!**
* Trên giao diện Web của chúng ta, người dùng sẽ KHÔNG CẦN nhập Private Key. Web chỉ có ô nhập số lượng tiền: *"Tôi muốn chuyển 10 BTC cho Bob"*.
* Khi bấm nút Gửi, Web chỉ truyền đi một thông điệp vô hại: `{"so_tien": 10, "nguoi_nhan": "Bob"}`. Đoạn tin nhắn này có bị Hacker bắt được cũng vô giá trị.
* Tin nhắn bay về trụ sở Backend (Flask). Backend lẳng lặng mở một cái két sắt giấu kín trong ổ cứng Server (gọi là file `.env` hoặc Biến môi trường). Nó lấy mã PIN (WIF) từ trong két sắt ra, tự động Ký tên vào giao dịch, rồi cất mã PIN đi. 
* Mã PIN không bao giờ rời khỏi chiếc két sắt của Server, cực kỳ an toàn!
