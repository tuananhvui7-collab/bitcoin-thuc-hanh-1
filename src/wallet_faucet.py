import os
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey
from bitcoinutils.proxy import NodeProxy

# Cấu hình kết nối RPC (đọc từ biến môi trường để chạy được cả local & Docker)
RPC_HOST = os.environ.get("RPC_HOST", "127.0.0.1")
RPC_PORT = os.environ.get("RPC_PORT", "18443")
RPC_USER = os.environ.get("RPC_USER", "dev")
RPC_PASSWORD = os.environ.get("RPC_PASSWORD", "devpass")

# Khởi tạo proxy để gọi RPC tới Node
proxy = NodeProxy(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT).get_proxy()

def derive_all_address_types(wif_or_new: str | None = None) -> dict:
    """
    Từ 1 private key, trả về dict chứa 4 loại địa chỉ:
    {"legacy": ..., "nested_segwit": ..., "native_segwit": ..., "taproot": ...}

    TODO (Dành cho bạn tự viết):
    1. setup('regtest')  # Bắt buộc gọi trước khi dùng thư viện
    2. Tạo PrivateKey (từ `wif_or_new` nếu có, hoặc tạo random nếu truyền vào None)
    3. Lấy public key từ private key
    4. Sinh ra từng loại địa chỉ bằng cách gọi phương thức tương ứng của public key
       (Tham khảo examples của python-bitcoin-utils trên github)
    5. Trả về dictionary chứa 4 địa chỉ
    """
    raise NotImplementedError("Bạn cần hoàn thành hàm này!")

def fund_address(address: str, num_blocks: int = 1):
    """Đào block, coinbase reward gửi thẳng vào address này."""
    return proxy.generatetoaddress(num_blocks, address)

if __name__ == "__main__":
    # Để dễ debug, tôi cung cấp sẵn một chuỗi WIF cố định.
    # Bạn có thể dùng chuỗi này, để mỗi lần chạy hàm luôn ra các địa chỉ giống nhau.
    FIXED_WIF = "cTALNpTpRbbxTCbD2JQjM85YMM7V9D4tLrtZRE37K4pGfL1G6YQy" 
    
    # 1. Gọi hàm sinh địa chỉ (hiện tại sẽ báo lỗi vì hàm chưa có logic)
    print("Đang tạo địa chỉ...")
    # addresses = derive_all_address_types(FIXED_WIF)
    # print(addresses)

    # 2. Vòng lặp: Nạp cho cả 4 loại địa chỉ, mỗi loại 1 block
    # for addr_type, addr in addresses.items():
    #     fund_address(addr, 1)
    
    # 3. Đào thêm 100 block "đệm" để coin "trưởng thành" (có thể tiêu được)
    # fund_address(addresses["legacy"], 100)
    
    # print("Đã đào xong 104 block! Các địa chỉ đã có tiền.")
