import os
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, P2shAddress
from bitcoinutils.proxy import NodeProxy
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

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

def sign_transaction_inputs(
    tx: Transaction, 
    priv_key: PrivateKey, 
    selected_utxos: list,
    address_type: str
) -> Transaction:
    """
    Ký điện tử cho toàn bộ Input trong Giao dịch, tách biệt 4 loại địa chỉ.
    """
    #Sinh khóa public.
    pub = priv_key.get_public_key()
    
    # 1. Tái tạo Script của ví để dùng cho việc ký (Thay vì parse hex từ node)
    if address_type == "legacy":
        script_pubkey = pub.get_address().to_script_pub_key()
    elif address_type == "nested_segwit":
        # Với Nested SegWit, ta ký trên Redeem Script (chính là Native Segwit Script)
        script_pubkey = pub.get_segwit_address().to_script_pub_key()
    elif address_type == "native_segwit":
        script_pubkey = pub.get_segwit_address().to_script_pub_key()
    elif address_type == "taproot":
        script_pubkey = pub.get_taproot_address().to_script_pub_key()
    else:
        raise ValueError(f"Không hỗ trợ ký cho loại địa chỉ: {address_type}")

    # 2. Chuẩn bị mảng Scripts và Amounts cho riêng thuật toán Schnorr (Taproot)
    utxo_scripts = [script_pubkey] * len(selected_utxos)
    utxo_amounts = [to_satoshis(utxo["amount"]) for utxo in selected_utxos]

    # 3. Ký điện tử cho từng tờ tiền (Input)
    for index, utxo in enumerate(selected_utxos):
        
        if address_type == "legacy":
            # Thuật toán ECDSA cơ bản
            priv_key.sign_input(tx, index, script_pubkey)
            
        elif address_type in ["nested_segwit", "native_segwit"]:
            # Thuật toán ECDSA kiểu Segwit (bắt buộc truyền thêm amount)
            priv_key.sign_segwit_input(tx, index, script_pubkey, to_satoshis(utxo["amount"]))
            
        elif address_type == "taproot":
            # Thuật toán Schnorr tối tân (bắt buộc truyền mảng Script và mảng Amount của TOÀN BỘ inputs)
            priv_key.sign_taproot_input(tx, index, utxo_scripts, utxo_amounts)
            
    return tx

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
    try:
        selected_utxos, total_gathered = select_utxos(alice_utxos, target)
        
        print(f"-> Đã bốc được {len(selected_utxos)} tờ tiền (UTXO).")
        print(f"-> Tổng giá trị xấp tiền bốc được: {total_gathered} BTC.")
        
        # 6. Tính toán tiền thừa (Change Output)
        change_amount = total_gathered - target
        print(f"-> Tiền thừa thối lại Alice: {change_amount} BTC")
        
    except ValueError as e:
        print(e)
