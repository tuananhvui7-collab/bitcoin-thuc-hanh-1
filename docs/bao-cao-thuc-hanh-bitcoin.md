# BÁO CÁO THỰC HÀNH: TƯƠNG TÁC VỚI BITCOIN
### Deploy Bitcoin full node trên local network (Testnet4)
**Môn học:** Tiền số và công nghệ Blockchain — Fintech, PTIT

---

## MỤC LỤC
1. Kiến trúc mạng Bitcoin — các loại node
2. Mô hình UTXO
3. Cơ chế đào coin (Proof of Work)
4. Mempool và vòng đời giao dịch
5. Điều chỉnh độ khó & Halving
6. Bảo mật mật mã học (ECC/ECDSA)
7. Các cơ chế mở rộng (SegWit, Taproot, Lightning, HD Wallet)
8. Fork và các loại tấn công mạng
9. Merkle Tree & SPV
10. So sánh cơ chế đồng thuận (PoW/PoS/PoA)
11. Nền tảng lý thuyết: Bài toán Byzantine Generals & Double-spending
12. Triển khai thực hành trên Testnet4
13. Checklist bằng chứng nộp báo cáo
14. Nguồn tham khảo

---

## 1. Kiến trúc mạng Bitcoin — các loại node

| Loại node | Lưu trữ | Vai trò | Analogy |
|---|---|---|---|
| **Light node (SPV)** | Chỉ block header + giao dịch của ví mình | Ví người dùng cuối, phụ thuộc full node | App ngân hàng — chỉ xem số dư |
| **Full/Archive node** | Toàn bộ blockchain từ block 0 | Xác thực mọi giao dịch, mọi block | Chi nhánh ngân hàng giữ bản sao sổ cái đầy đủ |
| **Mining node** | Full node + phần cứng đào | Tạo block mới bằng PoW | Nhân viên xử lý + đóng dấu xác nhận |
| **Participant** | Tuỳ loại ví | Gửi/nhận giao dịch | Khách hàng |

**Full node** validate mọi giao dịch/block và relay cho các node khác. **Pruned node** vẫn là full node thật (validate toàn bộ chain từ gốc) nhưng xoá dữ liệu cũ sau khi xác thực — giảm dung lượng từ hơn 700GB xuống còn ~7GB, đổi lại không phục vụ được lịch sử block cho light node khác và không tương thích với `-txindex`.

---

## 2. Mô hình UTXO (Unspent Transaction Output)

Bitcoin không có "số dư" như ngân hàng — ví là tập hợp các UTXO (giống nhiều tờ tiền mệnh giá lẻ). Không thể tách nhỏ 1 UTXO; phải tiêu nguyên cả UTXO rồi nhận lại phần dư ("change") thành UTXO mới.

```
5 BTC = UTXO1(1) + UTXO2(2) + UTXO3(2)
Chuyển 3.5 BTC → dùng UTXO2+UTXO3 = 4 BTC → trả lại 0.5 BTC (UTXO change mới)
```

Mỗi UTXO có "ổ khoá" `scriptPubKey` (điều kiện tiêu được nó). Khi tiêu, người gửi cung cấp `scriptSig` (chữ ký + public key) để "mở khoá". Node ghép 2 script lại và thực thi; nếu đúng, giao dịch hợp lệ và vào mempool.

---

## 3. Cơ chế đào coin (Proof of Work)

Đào coin **không phải mục đích chính** mà là **phần thưởng** cho việc xác nhận giao dịch. Thợ đào gộp các giao dịch đang chờ thành 1 block nháp, thử hàng tỷ giá trị `nonce` (số 32-bit, từ 0 đến 2³²-1) sao cho hash SHA-256 của cả block header đủ nhỏ (nhiều số 0 đầu). Không có công thức tính ngược — chỉ có thể brute-force, đây là lý do cần GPU/ASIC thay vì CPU.

Mỗi block luôn có tối thiểu 1 giao dịch đặc biệt — **coinbase transaction** (tự sinh ra, trả thưởng cho thợ đào) — nên "block rỗng" (không giao dịch người dùng) vẫn hợp lệ.

**51% Attack**: nếu 1 bên kiểm soát >50% sức mạnh đào của mạng, có thể đào nhanh hơn phần còn lại, tạo chain dài hơn để ghi đè lịch sử (double-spend). Bitcoin an toàn nhờ quy mô mạng quá lớn.

---

## 4. Mempool và vòng đời giao dịch

```
Gửi giao dịch → vào mempool (chờ) → thợ đào chọn (ưu tiên phí cao)
→ gộp vào block nháp → tìm nonce (đào) → block hợp lệ → rời mempool, ghi vĩnh viễn vào chain
```

Mempool là bộ nhớ tạm **của riêng từng node** — không phải 1 cấu trúc toàn cục, nên các node có thể thấy tập giao dịch chờ hơi khác nhau.

---

## 5. Điều chỉnh độ khó & Halving

- **Difficulty Adjustment**: cứ mỗi 2016 block (~2 tuần), mạng so sánh thời gian đào thực tế với mục tiêu (10 phút/block) để tăng/giảm độ khó, tối đa 4 lần tăng hoặc giảm 75% mỗi lần điều chỉnh.
- **Halving**: cứ mỗi 210.000 block (~4 năm), phần thưởng đào giảm một nửa — cách kiểm soát tổng cung 21 triệu BTC, viết cứng trong code.

---

## 6. Bảo mật mật mã học (ECC/ECDSA)

### Đường cong Elliptic
Công thức chuẩn: `y² = x³ + ax + b (mod p)`. Với Bitcoin: `a=0, b=7` → `y² = x³ + 7 (mod p)` — gọi là đường cong **secp256k1**. `p` là số nguyên tố 256-bit; mọi phép tính lấy dư theo p (finite field).

### Vì sao dùng được để mã hoá
`Public key = Private key × P` (P là điểm gốc cố định, phép nhân điểm trên đường cong). Chiều thuận (private→public) tính nhanh; chiều ngược (public→private) gần như không thể — đây là bài toán logarit rời rạc trên đường cong elliptic (ECDLP), nền tảng bảo mật.

### ECDSA — quy trình ký
1. Chọn private key ngẫu nhiên
2. Tính public key = private key × P
3. Ký: dùng private key + số ngẫu nhiên tạm `k` (nonce) → sinh cặp `(r, s)`
4. Verify: dùng public key kiểm tra `(r, s)` mà không cần biết private key

### DRBG — vì sao số ngẫu nhiên `k` khi ký quan trọng
Nếu `k` bị đoán được hoặc lặp lại giữa 2 chữ ký → **lộ private key** (từng xảy ra thật, làm lộ khoá ký firmware PS3 của Sony). Giải pháp: chuẩn **RFC 6979** dùng DRBG (Deterministic Random Bit Generator) sinh `k` xác định từ private key + nội dung message qua HMAC — mỗi message ra `k` khác nhau nhưng không cần xin số ngẫu nhiên thật từ hệ điều hành.

### Canonical form (low-S) — chống transaction malleability
Với 1 message, cả `(r, s)` và `(r, n-s)` đều là chữ ký hợp lệ (n = bậc đường cong) — đây từng là lỗ hổng: đổi `s` thành `n-s` làm đổi TXID dù nội dung không đổi. Bitcoin (BIP 62/146) quy định bắt buộc dùng giá trị `s` **nhỏ hơn** trong 2 khả năng.

### Vì sao Bitcoin không dùng secp256r1 (đường cong HTTPS dùng)
- **secp256r1** (NIST, dùng trong TLS/HTTPS): tham số được chọn "ngẫu nhiên" bởi 1 tổ chức — nghi ngờ có thể có cửa hậu (backdoor), dù chưa chứng minh được.
- **secp256k1** (Bitcoin dùng): tham số cố định, minh bạch, không do ai "chọn ngẫu nhiên" — ưu tiên niềm tin hơn chuẩn phổ biến của chính phủ Mỹ, đổi lại tính toán nhanh hơn.

### RSA vs ECC
| | RSA | ECC (Bitcoin) |
|---|---|---|
| Bài toán khó | Phân tích thừa số nguyên tố | Logarit rời rạc trên đường cong |
| Độ dài khoá (cùng mức bảo mật) | ~3072 bit | ~256 bit |
| Tốc độ | Chậm hơn | Nhanh hơn, gọn hơn |

**Post-Quantum**: cả RSA lẫn ECC đều bị phá vỡ nếu máy tính lượng tử đủ mạnh ra đời (thuật toán Shor) — Bitcoin hiện chưa áp dụng mã hoá hậu lượng tử.

---

## 7. Các cơ chế mở rộng

- **SegWit**: tách chữ ký ra khỏi dữ liệu chính giao dịch, sửa lỗi transaction malleability — điều kiện cần để Lightning Network hoạt động.
- **Taproot**: dùng chữ ký Schnorr + MAST, giao dịch phức tạp (multi-sig) trông giống giao dịch đơn giản → tăng riêng tư, giảm phí.
- **Địa chỉ**: `1...` (Legacy) → `bc1q...` (Native SegWit, testnet: `tb1q...`) → `bc1p...` (Taproot).
- **Lightning Network**: giải pháp Layer 2, dùng kênh thanh toán (payment channel) để giao dịch off-chain, giải quyết off-chain rồi mới ghi tổng kết lên chain.
- **HD Wallet (BIP32/39/44)**: BIP39 định nghĩa cách sinh cụm 12-24 từ (seed phrase); BIP32 cho phép 1 khoá gốc sinh vô số khoá con theo cây; BIP44 thêm đường dẫn để 1 seed quản lý nhiều loại coin.
- **Bitcoin không Turing-complete**: ngôn ngữ script cố tình không đủ mạnh để viết chương trình phức tạp (không vòng lặp) — khác Ethereum. Đây là lý do các giải pháp mở rộng phải xây "Layer 2" chồng lên trên thay vì sửa trực tiếp Layer 1.

---

## 8. Fork và các loại tấn công mạng

- **Soft fork**: nâng cấp tương thích ngược, không chia tách chuỗi (vd: SegWit).
- **Hard fork**: thay đổi không tương thích ngược, tách hẳn thành coin mới (vd: Bitcoin Cash).
- **Sybil/Eclipse Attack**: tấn công ở tầng P2P — tạo nhiều danh tính giả để can thiệp giao thức. Eclipse attack nhắm vào 1 node cụ thể, cô lập hoàn toàn kết nối của nó, có thể lừa double-spend.

---

## 9. Merkle Tree & SPV

Merkle tree: gộp từng cặp giao dịch, hash với nhau, lặp lại đến khi còn 1 hash duy nhất (merkle root). Nhờ đó, light node (SPV) chỉ cần tải block header + xin "Merkle proof" từ full node để xác minh 1 giao dịch cụ thể nằm trong block, không cần tải toàn bộ block.

---

## 10. So sánh cơ chế đồng thuận

| | PoW (Bitcoin) | PoS | PoA |
|---|---|---|---|
| Ai tạo block | Ai giải hash trước | Ai stake nhiều/được chọn theo stake | Nhóm định danh sẵn, được tin tưởng |
| Chi phí | Tốn điện, phần cứng | Gần như không tốn điện | Rất rẻ |
| Phi tập trung | Cao nhất | Trung bình | Thấp nhất |
| Phù hợp | Mạng công khai, không cần tin ai | Mạng công khai muốn tiết kiệm năng lượng | Mạng riêng tư/doanh nghiệp |

---

## 11. Nền tảng lý thuyết

### Bài toán Byzantine Generals (1982)
Nhiều vị tướng bao vây thành phố, chỉ liên lạc qua người đưa tin, cần đồng thuận tấn công cùng lúc — nhưng có tướng phản bội cố tình phá đồng thuận. Đây chính là vấn đề của Bitcoin: hàng nghìn node lạ cần đồng thuận về 1 lịch sử giao dịch duy nhất dù có kẻ xấu trong mạng.

**Bitcoin giải bằng PoW**: thay "1 người 1 phiếu" (dễ giả mạo bằng nhiều danh tính ảo — Sybil attack) bằng "1 đơn vị sức mạnh tính toán = 1 phiếu". Muốn nói dối cả mạng phải sở hữu >50% sức mạnh tính toán — quá tốn kém. Satoshi là người đầu tiên giải được bài toán này trong 1 mạng mở, không cần xin phép ai tham gia.

### Double-spending Problem
Vấn đề gốc của tiền số: ngăn 1 người tiêu 2 lần cùng 1 đồng coin (dữ liệu số dễ copy). Giải bằng: mọi node thấy chung 1 lịch sử giao dịch; giao dịch trùng UTXO đến sau sẽ bị từ chối.

### Block Confirmation
1 giao dịch nằm trong block mới nhất = "1 confirmation". Càng nhiều block chồng lên sau, càng khó đảo ngược. Quy ước phổ biến: **6 confirmations** = an toàn cho giao dịch giá trị lớn.

---

## 12. Triển khai thực hành trên Testnet4

> ⚠️ **Testnet3 (`-testnet`) đã bị loại bỏ hoàn toàn từ Bitcoin Core bản 30.0.** Dùng **Testnet4** (`-testnet4`), theo BIP 94, thay thế từ Bitcoin Core 28.0.

**Thông số Testnet4:** RPC port `48332`, P2P port `48333`, thư mục dữ liệu mặc định `~/.bitcoin/testnet4/`.

**Lưu ý về đào coin trên testnet4**: có rule "20 phút không có block → block tiếp theo bắt buộc về độ khó tối thiểu" (cho phép CPU đào), nhưng rule này **đang bị khai thác nặng** (~85-90% block do CPU đào ở độ khó tối thiểu) khiến giao dịch thật đôi khi phải chờ ~1 tiếng mới được block ASIC thật xác nhận. → Ưu tiên xin coin từ **faucet** thay vì tự đào để demo nhanh.

### A. Setup Full/Archive node
```bash
bitcoind -testnet4=1 -txindex=1 -daemon
bitcoin-cli -testnet4 getblockchaininfo
```
Giảm dung lượng (pruned node, để so sánh trong báo cáo):
```bash
bitcoind -testnet4=1 -prune=550 -daemon
```

### B. Setup Light node thật (SPV) — Electrs + Sparrow Wallet
```bash
git clone https://github.com/romanz/electrs
cd electrs && cargo build --release
./target/release/electrs --network testnet4 --daemon-dir ~/.bitcoin
```
Cài **Sparrow Wallet** → Preferences → Server → **Private Electrum** → nhập IP/host + port Electrs. Tạo ví, nhận coin từ faucet testnet4.

→ Bằng chứng: so sánh dung lượng thư mục dữ liệu Sparrow (vài trăm MB, chỉ header) với `~/.bitcoin` (hàng chục GB) bằng `du -sh`.

### C. Mining node
Dùng `getblocktemplate` + `submitblock` trên chính node full, hoặc trỏ `cpuminer` vào node.

### D. Local Network — kiến trúc đề xuất
```
[Máy A: Full/Archive node testnet4 + Electrs]  ← trung tâm mạng local
        ↑ (Electrum protocol)         ↑ (P2P: addnode/connect)
[Máy B: Sparrow = Light node]   [Máy C: Full node phụ]
```
```bash
bitcoin-cli -testnet4 addnode "<IP máy kia>" add
```
Nếu chỉ có 1 máy: chạy nhiều `-datadir` khác nhau + cài thêm Sparrow/Electrs, vẫn đủ minh hoạ đúng khái niệm.

### E. Faucet testnet4
Tìm "testnet4 faucet" (vd: coinfaucet.eu/en/btc-testnet4) — dán địa chỉ ví Sparrow vào để nhận coin test.

---

## 13. Checklist bằng chứng nộp báo cáo

- [ ] Ảnh chụp `getblockchaininfo` của node full/archive đang đồng bộ testnet4
- [ ] Ảnh chụp Sparrow (light node) hiển thị đúng số dư, kèm so sánh dung lượng lưu trữ
- [ ] Log 2 node full trong LAN đồng bộ với nhau qua `addnode`
- [ ] 1 giao dịch thật: Sparrow gửi → `getrawmempool` → chờ đào → `getblock` xem trong block
- [ ] Giải thích UTXO/chữ ký/merkle root bằng dữ liệu thật từ giao dịch trên (`listunspent`, `getrawtransaction`, `getaddressinfo`)
- [ ] Giải thích khái niệm Byzantine Generals Problem — vì sao Bitcoin cần PoW
- [ ] So sánh PoW/PoS/PoA và giải thích lựa chọn của Bitcoin
- [ ] Giải thích ECDSA + secp256k1 (không cần chứng minh toán chi tiết, chỉ cần nắm ý chính: dễ tính xuôi, khó tính ngược)

---

## 14. Nguồn tham khảo chính

- Satoshi Nakamoto, *Bitcoin: A Peer-to-Peer Electronic Cash System* — bitcoin.org/bitcoin.pdf
- `developer.bitcoin.org` — tài liệu kỹ thuật chính thức (transactions, RPC reference, block chain)
- `bitcoin.org/en/full-node` — hướng dẫn deploy full node chính thức (do giảng viên cung cấp)
- BIP 94 (Testnet4), BIP 32/39/44 (HD Wallet), BIP 62/146 (canonical signature)
- RFC 6979 — Deterministic ECDSA/DSA (DRBG)
- Bitcoin Core release notes (28.0, 30.0) — thông số testnet4, loại bỏ testnet3

---

*Tài liệu này được tổng hợp lại trong quá trình tự học bù cho buổi giảng đã nghỉ ốm, dựa trên note gốc của giảng viên và các tài liệu kỹ thuật chính thức. Các phần thao tác cụ thể (lệnh, cổng, flag) nên được đối chiếu lại với `bitcoind -help` trên phiên bản Bitcoin Core thực tế cài đặt trước khi nộp bài.*
