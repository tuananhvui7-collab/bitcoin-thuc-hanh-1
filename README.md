# Bitcoin Thực Hành 1 — Antigravity Workspace (đã hiệu chỉnh)

⚠️ **Bản cập nhật quan trọng**: phiên bản trước của workspace này dựa trên hiểu lầm
(deploy full/light/mining node trên testnet4). Sau khi có tài liệu chính thức
"Simplified Flow" từ giảng viên, workspace đã được xây lại đúng bản chất: đây là
**bài lập trình trên regtest**, không phải bài deploy hạ tầng.

## Bài thực hành thật sự yêu cầu gì

1. Cài Bitcoin local network (**regtest**, không phải full node/testnet), đào block
   ngay lập tức qua RPC.
2. Từ 1 private key, suy ra 4 loại địa chỉ (Legacy/Nested SegWit/Native SegWit/Taproot).
3. Nạp coin cho từng địa chỉ bằng chính coinbase reward (đào block = "faucet").
4. Liệt kê UTXO theo từng loại địa chỉ.
5. Coin selection: chọn ít UTXO nhất đủ để gửi.
6. Ký từng UTXO (ECDSA cho legacy/segwit, Schnorr cho taproot).
7. Build transaction từng loại, gộp thành 1 raw transaction.
8. Broadcast lên blockchain (local).
9. Xây UI/UX web hoặc desktop.
10. Đóng gói toàn bộ bằng Docker Compose, chạy bằng 1 lệnh.

## Stack

- **Python** + `python-bitcoin-utils` — chủ động chọn thay vì Node.js/`bitcoinjs-lib`
  (dù `bitcoinjs-lib` phổ biến hơn trong cộng đồng) vì người dùng muốn tránh Node.js
  và đang muốn luyện Python.
- **Flask** cho backend + giao diện web.
- JS thuần tối thiểu ở trình duyệt (không Node.js, không npm).

## Cấu trúc

```
bitcoin-thuc-hanh-1/
├── AGENTS.md                          # Luật cho agent (bản đã hiệu chỉnh)
├── README.md
├── docker-compose.yml                 # 2 service: bitcoind (regtest) + app (Flask)
├── .env.example                       # Mẫu biến môi trường RPC — copy thành .env
├── .agents/
│   ├── rules/AGENTS.md                # Antigravity tự load
│   └── skills/
│       ├── bitcoin-regtest-lab/       # Bước 1-3: setup, đào block, derive địa chỉ
│       ├── bitcoin-tx-engineer/       # Bước 4-8: UTXO, coin selection, ký, build, broadcast
│       ├── bitcoin-webapp-ui/         # Bước 9: Flask + JS tối thiểu
│       └── bitcoin-docker-package/    # Bước 10: đóng gói Docker Compose
├── docs/
│   └── bao-cao-thuc-hanh-bitcoin.md   # Tài liệu lý thuyết nền (UTXO/ECDSA/địa chỉ...)
├── src/                                # Nơi viết code thật
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── templates/
│   └── static/
└── evidence/                          # Lưu output/ảnh chụp làm bằng chứng
```

## Điểm đặc biệt: workspace này được thiết kế để LUYỆN PYTHON, không chỉ chạy được bài

Trong `AGENTS.md`, agent được yêu cầu: với các hàm cốt lõi (derive địa chỉ, coin
selection, ký giao dịch), **không đưa code đầy đủ ngay** — chỉ đưa khung sườn hàm
+ API cần dùng, để bạn tự viết thân hàm và được review lại. Phần "lắp ráp" không
mang tính học thuật (Flask boilerplate, setup regtest) thì agent làm thẳng.

Nếu bạn đang gấp deadline và chỉ cần chạy được, cứ nói thẳng với agent ("tôi đang
gấp, viết luôn giúp tôi") — agent sẽ tôn trọng và đưa code đầy đủ ngay, không ép học
lúc không phù hợp.

## Vài prompt mẫu

- "Giúp tôi setup regtest node và đào vài block thử."
- "Hướng dẫn tôi viết hàm suy ra 4 loại địa chỉ từ 1 private key." (agent sẽ đưa khung sườn, không code full)
- "Tôi viết xong hàm coin selection rồi, review giúp tôi." (dán code)
- "Tôi đang gấp deadline, viết luôn code ký + build transaction giúp tôi."
- "Giúp tôi làm giao diện Flask đơn giản cho bước cuối."
- "Đóng gói project này bằng Docker giúp tôi."
