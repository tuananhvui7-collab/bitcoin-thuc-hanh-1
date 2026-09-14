import os
from decimal import Decimal
from bitcoinutils.keys import PrivateKey, P2shAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

from tx_builder import (
    derive_all_address_types, 
    get_utxos_by_address, 
    select_utxos, 
    sign_transaction_inputs
)

def run_comprehensive_test():
    print("🚀 KHỞI ĐỘNG BỘ TEST TOÀN DIỆN THUẬT TOÁN KÝ (4 LOẠI ĐỊA CHỈ)\n")
    
    ALICE_WIF = "cSmKSQgPLqn9jSt89KjbhTiBpT7qK4jWrdQnmgMzHPuhZvVbp82V"
    BOB_WIF = "cUi51ejxfidY9JMwFg8orA1zFFhHCwyGtsKcb42gaTPRScGrVNGJ"
    
    alice_priv = PrivateKey(ALICE_WIF)
    bob_priv = PrivateKey(BOB_WIF)
    
    address_types = ["legacy", "nested_segwit", "native_segwit", "taproot"]
    target_amount = Decimal("10.0") # Gửi 10 BTC
    
    for addr_type in address_types:
        print(f"--- ĐANG TEST NHÁNH: {addr_type.upper()} ---")
        try:
            # 1. Quét tiền của Alice
            alice_addr_string = derive_all_address_types(ALICE_WIF)[addr_type]
            utxos_data = get_utxos_by_address(alice_addr_string)
            utxos_list = utxos_data.get('unspents', [])
            
            if not utxos_list:
                print(f"⚠️ Alice không có UTXO ở ví {addr_type}. Bỏ qua test nhánh này.\n")
                continue
                
            # 2. Bốc tiền
            selected_utxos, total = select_utxos(utxos_list, target_amount)
            change = total - target_amount
            
            # 3. Tạo Inputs
            tx_inputs = [TxInput(u["txid"], u["vout"]) for u in selected_utxos]
            
            # 4. Tạo Outputs (Bob nhận 10 BTC, Alice nhận tiền thừa)
            bob_pub = bob_priv.get_public_key()
            alice_pub = alice_priv.get_public_key()
            
            if addr_type == "legacy":
                bob_script = bob_pub.get_address().to_script_pub_key()
                alice_script = alice_pub.get_address().to_script_pub_key()
                is_segwit = False
            elif addr_type == "nested_segwit":
                bob_script = P2shAddress.from_script(bob_pub.get_segwit_address().to_script_pub_key()).to_script_pub_key()
                alice_script = P2shAddress.from_script(alice_pub.get_segwit_address().to_script_pub_key()).to_script_pub_key()
                is_segwit = True
            elif addr_type == "native_segwit":
                bob_script = bob_pub.get_segwit_address().to_script_pub_key()
                alice_script = alice_pub.get_segwit_address().to_script_pub_key()
                is_segwit = True
            elif addr_type == "taproot":
                bob_script = bob_pub.get_taproot_address().to_script_pub_key()
                alice_script = alice_pub.get_taproot_address().to_script_pub_key()
                is_segwit = True

            tx_outputs = [
                TxOutput(to_satoshis(target_amount), bob_script),
                TxOutput(to_satoshis(change), alice_script)
            ]
            
            # 5. Khung Giao Dịch
            tx = Transaction(tx_inputs, tx_outputs, has_segwit=is_segwit)
            
            # 6. GỌI HÀM KÝ ĐỂ TEST
            signed_tx = sign_transaction_inputs(tx, alice_priv, selected_utxos, addr_type)
            
            # 7. Kiểm tra kết quả
            hex_tx = signed_tx.serialize()
            print(f"✅ PASS! Hàm nhả ra Hex dài {len(hex_tx)} ký tự: {hex_tx[:30]}...\n")
            
        except Exception as e:
            print(f"❌ FAIL! Lỗi ở nhánh {addr_type}: {e}\n")

if __name__ == "__main__":
    run_comprehensive_test()
