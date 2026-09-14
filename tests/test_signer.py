import os
import sys
from decimal import Decimal
from bitcoinutils.keys import PrivateKey, P2shAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

# Thêm thư mục src vào đường dẫn hệ thống để import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from tx_builder import (
    derive_all_address_types, 
    get_utxos_by_address, 
    select_utxos, 
    sign_transaction_inputs,
    estimate_tx_fee,
    proxy
)

def run_comprehensive_test():
    print("🚀 KHỞI ĐỘNG BỘ TEST TOÀN DIỆN THUẬT TOÁN KÝ (4 LOẠI ĐỊA CHỈ)\n")
    
    ALICE_WIF = "cSmKSQgPLqn9jSt89KjbhTiBpT7qK4jWrdQnmgMzHPuhZvVbp82V"
    BOB_WIF = "cUi51ejxfidY9JMwFg8orA1zFFhHCwyGtsKcb42gaTPRScGrVNGJ"
    
    alice_priv = PrivateKey(ALICE_WIF)
    bob_priv = PrivateKey(BOB_WIF)
    
    # 0. TẠO VÍ CHO THỢ ĐÀO ĐỂ MINH HỌA
    miner_address = proxy.getnewaddress("Ví của Thợ Đào", "bech32")
    
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
                
            # [CẢI TIẾN] Bốc nháp 1 lần để đoán số lượng UTXO, sau đó tính phí ĐỘNG
            selected_utxos_draft, _ = select_utxos(utxos_list, target_amount)
            dynamic_fee = estimate_tx_fee(addr_type, len(selected_utxos_draft), 2)
            print(f"💡 Ước lượng phí động cho {len(selected_utxos_draft)} tờ tiền ({addr_type}): {dynamic_fee} BTC")
            
            # 2. Bốc tiền THẬT (Lấy đủ tiền gửi + tiền phí động)
            selected_utxos, total = select_utxos(utxos_list, target_amount + dynamic_fee)
            change = total - target_amount - dynamic_fee
            
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
            
            # 7. Kiểm tra kết quả (nhầm lẫn, bước 7 mới có.)
            hex_tx = signed_tx.serialize()
            print(f"✅ PASS KÝ TÊN! Hàm nhả ra Hex dài {len(hex_tx)} ký tự.")
            
            # 8. BƯỚC 7: PHÁT SÓNG VÀ XÁC MINH KÉP (tương tự, đây là bước 8 )
            print("Đang phát sóng lên mạng (Broadcast)...")
            try:
                # Gửi đi
                txid = proxy.sendrawtransaction(hex_tx)
                print(f"🎉 BROADCAST THÀNH CÔNG! Node đã trả về TXID: {txid}")
                
                # MINH HỌA SỰ XUẤT HIỆN CỦA THỢ ĐÀO
                print("⛏️ Miner đang đóng gói giao dịch này vào Block mới...")
                
                # Đào 1 block để chốt giao dịch
                proxy.generatetoaddress(1, miner_address) 
                
                # 9. MỔ XẺ BLOCK VỪA ĐÀO ĐƯỢC
                best_block_hash = proxy.getbestblockhash()
                block_info = proxy.getblock(best_block_hash)
                
                print(f"📦 Đã tạo thành công Block số {block_info['height']}!")
                print(f"   - Mã băm (Hash): {best_block_hash}")
                print(f"   - Giao dịch của Alice nầm ở vị trí số 2: {block_info['tx'][1]}")
                
                # Giao dịch đầu tiên (vị trí 0) luôn là Coinbase (Thợ đào nhận lương)
                coinbase_txid = block_info['tx'][0]
                coinbase_tx = proxy.getrawtransaction(coinbase_txid, True)
                miner_reward = coinbase_tx['vout'][0]['value']
                
                print(f"💰 CHI TIẾT LƯƠNG THỢ ĐÀO:")
                print(f"   - Coinbase TXID: {coinbase_txid}")
                print(f"   - Tổng thu nhập thực tế: {miner_reward} BTC (Gồm phần thưởng Block + {dynamic_fee} BTC tiền phí của Alice)")
                print("-" * 50 + "\n")
                
            except Exception as rpc_err:
                print(f"❌ NODE TỪ CHỐI GIAO DỊCH! Lý do: {rpc_err}")
                print("-" * 50 + "\n")
                
        except Exception as e:
            print(f"❌ FAIL! Lỗi ở nhánh {addr_type}: {e}\n")

if __name__ == "__main__":
    run_comprehensive_test()
