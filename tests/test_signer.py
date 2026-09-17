import os
import sys
from decimal import Decimal
from bitcoinutils.keys import PrivateKey, P2shAddress
from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.utils import to_satoshis

# Thêm thư mục src vào đường dẫn hệ thống để import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# pyrefly: ignore [missing-import]
from tx_builder import (
    derive_all_address_types, 
    build_and_sign_tx,
    proxy
)

def run_comprehensive_test():
    print("🚀 KHỞI ĐỘNG BỘ TEST TOÀN DIỆN THUẬT TOÁN KÝ (HỖ TRỢ MIX UTXO)\n")
    
    ALICE_WIF = "cSmKSQgPLqn9jSt89KjbhTiBpT7qK4jWrdQnmgMzHPuhZvVbp82V"
    BOB_WIF = "cUi51ejxfidY9JMwFg8orA1zFFhHCwyGtsKcb42gaTPRScGrVNGJ"
    
    alice_priv = PrivateKey(ALICE_WIF)
    bob_priv = PrivateKey(BOB_WIF)
    
    # 0. TẠO VÍ CHO THỢ ĐÀO (Dùng Private Key cục bộ để không phụ thuộc vào ví của Node)
    miner_priv = PrivateKey()
    miner_address = miner_priv.get_public_key().get_segwit_address().to_string()
    
    target_amount = Decimal("10.0") # Gửi 10 BTC
    
    # Lấy đại 1 địa chỉ của Bob (ví dụ Native Segwit) để làm đích đến
    bob_pub = bob_priv.get_public_key()
    bob_script = bob_pub.get_segwit_address().to_script_pub_key()
    
    print(f"--- ĐANG TEST LUỒNG CHUYỂN TIỀN (GOM UTXO TỪ NHIỀU VÍ) ---")
    try:
        # 1. GỌI API LÕI ĐỂ XÂY DỰNG VÀ KÝ GIAO DỊCH
        signed_tx, dynamic_fee, selected_utxos = build_and_sign_tx(
            sender_wif=ALICE_WIF,
            receiver_pub_script=bob_script,
            target_amount=target_amount
        )
        
        hex_tx = signed_tx.serialize()
        print(f"💡 Đã dùng {len(selected_utxos)} tờ tiền (UTXOs trộn lẫn), Phí động: {dynamic_fee} BTC")
        print(f"✅ PASS KÝ TÊN! Hàm nhả ra Hex dài {len(hex_tx)} ký tự.")
        
        # 2. PHÁT SÓNG VÀ XÁC MINH KÉP
        print("Đang phát sóng lên mạng (Broadcast)...")
        txid = proxy.sendrawtransaction(hex_tx)
        print(f"🎉 BROADCAST THÀNH CÔNG! Node đã trả về TXID: {txid}")
        
        print("⛏️ Miner đang đóng gói giao dịch này vào Block mới...")
        proxy.generatetoaddress(1, miner_address) 
        
        # 3. MỔ XẺ BLOCK VỪA ĐÀO ĐƯỢC
        best_block_hash = proxy.getbestblockhash()
        block_info = proxy.getblock(best_block_hash)
        
        print(f"📦 Đã tạo thành công Block số {block_info['height']}!")
        print(f"   - Mã băm (Hash): {best_block_hash}")
        print(f"   - Giao dịch của Alice nằm ở vị trí số 2: {block_info['tx'][1]}")
        
        coinbase_txid = block_info['tx'][0]
        coinbase_tx = proxy.getrawtransaction(coinbase_txid, True)
        miner_reward = coinbase_tx['vout'][0]['value']
        
        print(f"💰 CHI TIẾT LƯƠNG THỢ ĐÀO:")
        print(f"   - Coinbase TXID: {coinbase_txid}")
        print(f"   - Tổng thu nhập thực tế: {miner_reward} BTC (Gồm phần thưởng Block + {dynamic_fee} BTC tiền phí của Alice)")
        print("-" * 50 + "\n")
            
    except Exception as e:
        print(f"❌ FAIL! Lỗi: {e}\n")

if __name__ == "__main__":
    run_comprehensive_test()
