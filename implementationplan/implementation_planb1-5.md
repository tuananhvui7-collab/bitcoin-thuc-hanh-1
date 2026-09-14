# Kế hoạch thực hiện: Đào block bằng RPC và nạp tiền (Faucet)

Tiếp theo, chúng ta sẽ thực hiện các bước 2 và 3 trong sơ đồ (Simplified Flow): 
- **Bước 2**: Từ 1 private key, suy ra tất cả các loại địa chỉ (Legacy, Nested SegWit, Native SegWit, Taproot).
- **Bước 3**: "Faucet" nạp coin cho từng địa chỉ bằng cách dùng node đào block (mine block) trực tiếp vào các địa chỉ này qua RPC.

> [!IMPORTANT]  
> Theo quy tắc của bài thực hành, mục tiêu chính là để bạn **luyện tập code Python**. Vì vậy, tôi sẽ chuẩn bị sẵn phần kết nối RPC (hạ tầng), nhưng sẽ chỉ cung cấp **khung sườn (skeleton)** cho các hàm tạo địa chỉ. Bạn sẽ là người điền logic cho các hàm đó dựa trên tài liệu tham khảo.

## User Review Required

Vui lòng xem qua kế hoạch dưới đây. Nếu bạn đồng ý, tôi sẽ tạo file code mẫu, sau đó bạn sẽ bắt đầu hoàn thiện nó.

## Proposed Changes

Tôi sẽ thực hiện các thao tác sau:

### 1. Tạo ví (wallet) trên Node Regtest
Node Bitcoin regtest hiện chưa có ví (wallet) nào cả. Để chạy được lệnh đào block `generatetoaddress`, node cần có ít nhất một ví đang load.
Tôi sẽ chạy lệnh sau trong docker để tạo ví tên là `lab`:
`docker exec btc-regtest-node bitcoin-cli -regtest -rpcuser=dev -rpcpassword=devpass createwallet "lab"`

### 2. Tạo script Python: `src/wallet_faucet.py`
Tôi sẽ tạo file `src/wallet_faucet.py` chứa:
- **Phần kết nối RPC:** Dùng `NodeProxy` của thư viện `bitcoin-utils` và đọc host, port từ biến môi trường.
- **Khung hàm `derive_all_address_types()`**: Trả về 4 loại địa chỉ từ private key. **Đây là phần bạn sẽ phải tự code**.
- **Hàm `fund_address(address, num_blocks)`**: Hàm thực hiện gọi RPC `generatetoaddress` để đào block cho địa chỉ đích. Tôi sẽ code luôn phần này vì đây chỉ là gọi API RPC đơn giản.
- **Kịch bản chính**: Nạp cho 4 địa chỉ (mỗi loại 1 block) và đào thêm 100 block "đệm" để tiền đủ điều kiện tiêu (coinbase reward cần 100 confirmations).

## Open Questions

- Ở bước tạo địa chỉ, bạn có muốn dùng một **Private Key cố định** (theo chuẩn WIF) cho mọi lần chạy để các địa chỉ sinh ra luôn giống nhau (dễ debug/theo dõi UTXO sau này) hay muốn sinh ngẫu nhiên mỗi lần chạy? Khuyến nghị: **Dùng cố định**.
