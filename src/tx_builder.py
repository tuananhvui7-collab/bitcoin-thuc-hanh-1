import os
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, P2shAddress
from bitcoinutils.proxy import NodeProxy

# Cấu hình kết nối RPC
RPC_HOST = os.environ.get("RPC_HOST", "127.0.0.1")
RPC_PORT = os.environ.get("RPC_PORT", "18443")
RPC_USER = os.environ.get("RPC_USER", "dev")
RPC_PASSWORD = os.environ.get("RPC_PASSWORD", "devpass")

setup('regtest')

proxy = NodeProxy(RPC_USER, RPC_PASSWORD, RPC_HOST, RPC_PORT)

# Copy lại hàm sinh địa chỉ từ file trước để dùng lại
def derive_all_address_types(wif: str) -> dict:
    priv = PrivateKey(wif)
    pub = priv.get_public_key()
    
    p2wpkh = pub.get_segwit_address()
    
    return {
        "legacy": pub.get_address().to_string(),
        "nested_segwit": P2shAddress.from_script(p2wpkh.to_script_pub_key()).to_string(),
        "native_segwit": p2wpkh.to_string(),
        "taproot": pub.get_taproot_address().to_string()
    }

def get_utxos_by_address(address:str) -> dict:
    #Lệnh  scantxoutset yêu cầu cần cung cấp cho nó 1 mảng các descriptor.
    # scan_request là 1 list bên trong chứa 1 dict (ScanObjects)
    # desc là viết tắt của Descriptor: ngôn ngữ chuẩn bitcoin để khai báo xem bạn làm gì. 
    # VÍ dụ: addr(mk9UxMD...): là khai báo "cho tôi xem UTXO của  địa chỉ này"

    scan_request = [{"desc": f"addr({address})"}]
    result = proxy.scantxoutset("start", scan_request)
    return result
    
from decimal import Decimal

def select_utxos(utxos: list, target_amount: Decimal) -> tuple[list, Decimal]:
    """
    Thuật toán Largest-First: Chọn các UTXO lớn nhất để tối thiểu hóa số lượng UTXO, 
    giúp giảm dung lượng giao dịch và tiết kiệm phí mạng lưới.
    """
    sorted_utxos = sorted(utxos, key=lambda x: x["amount"], reverse=True)
    
    selected = []
    total_gathered = Decimal('0.0')
    
    for utxo in sorted_utxos:
        selected.append(utxo)
        total_gathered += Decimal(str(utxo["amount"]))
        
        if total_gathered >= target_amount:
            return selected, total_gathered
            
    raise ValueError(f"Alice không đủ tiền! Cần {target_amount} BTC nhưng chỉ có {total_gathered} BTC.")

if __name__ == "__main__":
    # 1. Tác nhân Alice (Người gửi - Đang giàu)
    ALICE_WIF = "cSmKSQgPLqn9jSt89KjbhTiBpT7qK4jWrdQnmgMzHPuhZvVbp82V"
    alice_addresses = derive_all_address_types(ALICE_WIF)
    
    # 2. Tác nhân Bob (Người nhận - Đang nghèo)
    BOB_WIF = "cUi51ejxfidY9JMwFg8orA1zFFhHCwyGtsKcb42gaTPRScGrVNGJ"
    bob_addresses = derive_all_address_types(BOB_WIF)
    
    # 3. Kịch bản: Alice lấy tiền từ ví Taproot để gửi cho Bob (Native Segwit)
    print("=== THÔNG TIN VÍ ===")
    alice_balance = get_utxos_by_address(alice_addresses["taproot"]).get("total_amount", 0)
    bob_balance = get_utxos_by_address(bob_addresses["native_segwit"]).get("total_amount", 0)
    
    print(f"Ví Taproot của Alice: {alice_addresses['taproot']} (Số dư: {alice_balance} BTC)")
    print(f"Ví Native Segwit của Bob: {bob_addresses['native_segwit']} (Số dư: {bob_balance} BTC)")
    
    # 4. Gom tiền từ ví Taproot của Alice
    utxo_data = get_utxos_by_address(alice_addresses["taproot"])
    alice_utxos = utxo_data.get("unspents", [])
    
    # 5. Alice muốn trả 90 BTC cho Bob + 0.001 BTC cho Thợ đào
    target = Decimal("90.001") 
    
    print(f"\n=== MÔ PHỎNG COIN SELECTION ===")
    print(f"Alice đang cố gắng nhặt ra {target} BTC từ ví Taproot...")
    selected_utxos, total_gathered = select_utxos(alice_utxos, target)
    
    print(f"-> Đã bốc được {len(selected_utxos)} tờ tiền (UTXO).")
    print(f"-> Tổng giá trị xấp tiền bốc được: {total_gathered} BTC.")
    
    # 6. Tính toán tiền thừa (Change Output)
    change_amount = total_gathered - target
    print(f"-> Tiền thừa Alice sẽ nhận lại (Change): {change_amount} BTC.")

