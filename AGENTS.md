# AGENTS.md — Bài thực hành 1: Tương tác với Bitcoin (Regtest, Python)

## Bối cảnh dự án (ĐÃ HIỆU CHỈNH — quan trọng)
Đề bài chính thức của thầy ("Simplified Flow") yêu cầu:
1. Cài Bitcoin **local network kiểu regtest** (không phải full node đồng bộ thật,
   không phải testnet) — đào block ngay lập tức qua RPC (`generatetoaddress`).
2. Từ 1 private key, suy ra đủ 4 loại địa chỉ: Legacy (P2PKH), Nested SegWit
   (P2SH-P2WPKH), Native SegWit (P2WPKH), Taproot (P2TR).
3. Nạp coin cho từng loại địa chỉ bằng chính coinbase reward khi đào block
   ("faucet from miner" — không có faucet internet thật trong regtest).
4. Liệt kê UTXO của từng loại địa chỉ.
5. Coin selection: chọn tổ hợp UTXO **tối thiểu** đủ để gửi một khoản, giảm phí.
6. Ký từng UTXO riêng biệt (Legacy/SegWit dùng ECDSA, Taproot dùng Schnorr — khác
   thuật toán ký).
7. Build transaction cho từng loại địa chỉ (script khác nhau), gộp thành 1 raw
   transaction hex.
8. Broadcast qua `sendrawtransaction`.
9. Xây UI/UX web hoặc desktop.
10. **Đóng gói toàn bộ project bằng Docker** (node regtest + app) để chạy bằng 1
    lệnh `docker compose up`, không cần cài bitcoind/Python trực tiếp lên máy.

**KHÔNG** dùng testnet4, KHÔNG cần deploy full/light/mining node vật lý như hiểu
lầm ban đầu — bài này thuần về code, dùng đúng `bitcoind -regtest`.

## Stack đã chốt
- **Python** + thư viện **`python-bitcoin-utils`** (karask/python-bitcoin-utils) —
  hỗ trợ sẵn đủ 4 loại địa chỉ, multi-sighash, Taproot, PSBT, gọi RPC qua NodeProxy.
- **Flask** cho backend + phục vụ giao diện web.
- JavaScript **chỉ dùng tối thiểu** ở phía trình duyệt (gọi API bằng fetch, không
  cần Node.js, không cần npm) — người dùng chủ động tránh Node.js.
- **Docker Compose** với 2 service: `bitcoind` (image `bitcoin/bitcoin:28.0`, chạy
  `-regtest=1`) và `app` (build từ `src/`, chạy Flask). Mọi code kết nối RPC phải
  đọc host/port/credentials từ biến môi trường (`RPC_HOST`, `RPC_PORT`, `RPC_USER`,
  `RPC_PASSWORD`), KHÔNG hardcode `127.0.0.1` — vì bên trong Docker, node nằm ở
  hostname `bitcoind`, không phải localhost.

## QUAN TRỌNG NHẤT: người dùng muốn luyện Python qua bài này, không chỉ xin code chạy được

Đây là yêu cầu ưu tiên cao, áp dụng cho mọi skill trong dự án:

- Với các hàm **cốt lõi để học** (derive địa chỉ từ private key, thuật toán coin
  selection, vòng lặp ký từng input, build/serialize transaction) — **KHÔNG viết
  sẵn toàn bộ code rồi đưa** trừ khi người dùng xin thẳng "viết luôn giúp tôi" hoặc
  đang gấp deadline và nói rõ điều đó.
- Thay vào đó: giải thích logic cần làm bằng lời + tên hàm/API của
  `python-bitcoin-utils` cần dùng, để người dùng tự viết thân hàm. Đưa gợi ý dạng
  khung sườn (function signature + docstring + TODO), không đưa full implementation.
- Khi người dùng nộp code tự viết, review kỹ, chỉ ra lỗi/cách Python idiomatic hơn
  (list comprehension, context manager, type hint...) thay vì chỉ sửa im lặng.
- Các phần **không mang tính học thuật** (setup Flask boilerplate, cấu hình regtest,
  cài thư viện) — cứ làm thẳng, không cần biến thành bài tập.
- Nếu người dùng nói rõ đang gấp/mệt/chỉ muốn chạy được — tôn trọng, đưa code đầy đủ
  ngay, đừng ép học lúc không phù hợp.

## Nguyên tắc kỹ thuật khác
- Không tự đoán API của `python-bitcoin-utils` — kiểm tra ví dụ chính thức tại
  `github.com/karask/python-bitcoin-utils/tree/master/examples` trước khi hướng dẫn,
  vì thư viện đổi API giữa các bản.
- Luôn dùng `bitcoind -regtest` — không nhầm với `-testnet4` (bài trước đã nhầm 1
  lần, đã sửa).
- Mọi đoạn code kết nối RPC (trong bất kỳ skill nào) phải nhận host/port/user/pass
  qua biến môi trường, không hardcode — để chạy được cả khi dev trực tiếp lẫn khi
  chạy trong Docker (xem skill `bitcoin-docker-package`).
- Ngôn ngữ trả lời: tiếng Việt, hạn chế thuật ngữ Anh không cần thiết.
- Tài liệu lý thuyết nền (UTXO, ECDSA, địa chỉ...) đã có sẵn ở
  `docs/bao-cao-thuc-hanh-bitcoin.md` — tham chiếu, không giải thích lại từ đầu.

## Skill có sẵn
- `bitcoin-regtest-lab` — setup node regtest, đào block, suy ra 4 loại địa chỉ,
  nạp coin cho từng địa chỉ (bước 1-3).
- `bitcoin-tx-engineer` — liệt kê UTXO, coin selection, ký, build & broadcast
  transaction (bước 4-8) — **áp dụng chế độ "gợi ý dần" để luyện Python**.
- `bitcoin-webapp-ui` — Flask + giao diện web tối thiểu (bước 9).
- `bitcoin-docker-package` — đóng gói node + app bằng Docker Compose (bước 10) —
  phần hạ tầng, làm thẳng, không áp dụng chế độ gợi ý dần.
