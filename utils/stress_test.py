import time
import os
from decimal import Decimal
from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

def run_stress_test():
    print("🚀 KHỞI ĐỘNG CHIẾN DỊCH STRESS TEST (1000 Giao dịch)...")
    
    url = f"http://{os.getenv('RPC_HOST', '127.0.0.1')}:{os.getenv('RPC_PORT', 18443)}/"
    auth = HTTPBasicAuth(os.getenv('RPC_USER', 'dev'), os.getenv('RPC_PASSWORD', 'devpass'))
    
    def rpc_call(method, params=[]):
        payload = {"jsonrpc": "1.0", "id": "curltest", "method": method, "params": params}
        res = requests.post(url, json=payload, auth=auth)
        return res.json()

    print("Đang chuẩn bị Node Wallet (Đào 101 Block để có dư tiền)...")
    addr_res = rpc_call("getnewaddress")
    node_addr = addr_res.get('result')
    if not node_addr:
        # Có thể chưa có ví default, tạo 1 cái
        rpc_call("createwallet", ["default"])
        node_addr = rpc_call("getnewaddress").get('result')
        
    rpc_call("generatetoaddress", [101, node_addr])
    
    balance = rpc_call("getbalance").get('result', 0)
    print(f"Số dư Node Wallet: {balance} BTC")
    
    if balance < 0.2:
        print("Không đủ tiền để stress test! Vui lòng kiểm tra lại Node.")
        return
        
    print("\n🔥 BẮT ĐẦU SPAM MEMPOOL (1000 LỆNH CHUYỂN TIỀN)")
    print("Hãy mở Web App > Tab Trạm Thợ Đào để xem Mempool tăng vọt nhé!\n")
    
    # Tạo địa chỉ đích động thay vì hardcode để tương thích mọi phiên bản
    bob_pub = rpc_call("getnewaddress").get('result') 
    
    success_count = 0
    for i in range(1, 1001):
        res = rpc_call("sendtoaddress", [bob_pub, 0.0001])
        if res.get('error'):
            print(f"Lỗi ở giao dịch {i}:", res['error'])
            # Nếu Node hết UTXO để xé lẻ, ta đào 1 block để xác nhận tiền thừa
            if "Insufficient funds" in str(res['error']):
                rpc_call("generatetoaddress", [1, node_addr])
        else:
            success_count += 1
            if i % 100 == 0:
                print(f"🚀 Đã bắn thành công {i} giao dịch vào Mempool...")
                
    print(f"\n✅ ĐÃ HOÀN TẤT SPAM! Tổng cộng: {success_count} giao dịch.")
    print("Vui lòng lên Web App để tự tay bấm nút 'TẠO BLOCK MỚI & THU PHÍ' và dọn dẹp Mempool nhé!")

if __name__ == "__main__":
    run_stress_test()
