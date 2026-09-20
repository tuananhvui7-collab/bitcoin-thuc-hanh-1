import time
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

def run_reorg_simulation():
    print("🚀 KHỞI ĐỘNG KỊCH BẢN TẤN CÔNG 51% (CHAIN REORG)...\n")
    
    url = f"http://{os.getenv('RPC_HOST', '127.0.0.1')}:{os.getenv('RPC_PORT', 18443)}/"
    auth = HTTPBasicAuth(os.getenv('RPC_USER', 'dev'), os.getenv('RPC_PASSWORD', 'devpass'))
    
    def rpc_call(method, params=[]):
        payload = {"jsonrpc": "1.0", "id": "curltest", "method": method, "params": params}
        res = requests.post(url, json=payload, auth=auth)
        return res.json()

    # 1. Đảm bảo Mempool có giao dịch để đóng vào Block
    print("1. Đang tạo 5 giao dịch mồi vào Mempool...")
    addr_res = rpc_call("getnewaddress")
    node_addr = addr_res.get('result')
    if not node_addr:
        rpc_call("createwallet", ["default"])
        node_addr = rpc_call("getnewaddress").get('result')
    
    bob_pub = rpc_call("getnewaddress").get('result')
    
    for i in range(5):
        rpc_call("sendtoaddress", [bob_pub, 0.001])
        
    mempool = rpc_call("getrawmempool").get('result', [])
    print(f"-> Mempool hiện tại có {len(mempool)} giao dịch.")
    
    # 2. Đào Block X chứa 5 giao dịch này
    print("\n2. Đang đào Block X để chốt 5 giao dịch trên...")
    hash_res = rpc_call("generatetoaddress", [1, node_addr])
    block_x_hash = hash_res.get('result', [])[0]
    print(f"-> Đã đóng Block X: {block_x_hash}")
    
    mempool = rpc_call("getrawmempool").get('result', [])
    print(f"-> Mempool hiện tại: {len(mempool)} giao dịch (Đã dọn sạch).")
    
    print("\n⏳ Chờ 10 giây để bạn có thể xem Sổ cái trên Web (Các giao dịch đang màu Xanh)...")
    time.sleep(10)
    
    # 3. Thực hiện InvalidateBlock (Reorg)
    print("\n🔥 3. THỰC HIỆN TẤN CÔNG 51%: Chối bỏ Block X (InvalidateBlock)!")
    rpc_call("invalidateblock", [block_x_hash])
    
    print("-> Đã ép mạng lưới hủy bỏ Block X.")
    
    # 4. Kiểm tra lại Mempool
    mempool_after = rpc_call("getrawmempool").get('result', [])
    print(f"\n✅ KẾT QUẢ: Mempool hiện tại có {len(mempool_after)} giao dịch.")
    print("Tất cả 5 giao dịch đã bị 'nôn' ngược trở lại Mempool vì Block X không còn tồn tại!")
    print("\nHãy mở Web App, bạn sẽ thấy các giao dịch vừa màu Xanh (Hoàn thành) nay đã lùi về màu Vàng (Đang chờ).")

if __name__ == "__main__":
    run_reorg_simulation()
