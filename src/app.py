import os
from decimal import Decimal
import time
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey, P2pkhAddress, P2shAddress, P2wshAddress, P2wpkhAddress, P2trAddress
from bitcoinutils.proxy import NodeProxy
from tx_builder import derive_all_address_types, get_utxos_by_address, build_and_sign_tx, proxy

app = Flask(__name__)
setup('regtest')

MINER_WIF = os.environ.get("MINER_WIF")
LOCKED_UTXOS = set()

HISTORY_FILE = 'history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history_list):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_list, f, indent=4)

# BỘ NHỚ SỔ CÁI (LEDGER) - Tải từ file JSON
TRANSACTION_HISTORY = load_history()

def get_total_balance(wif: str) -> dict:
    addresses = derive_all_address_types(wif)
    total = Decimal('0')
    
    for addr_type, addr in addresses.items():
        data = get_utxos_by_address(addr)
        for u in data.get('unspents', []):
            utxo_id = f"{u['txid']}:{u['vout']}"
            if utxo_id not in LOCKED_UTXOS:
                total += Decimal(str(u['amount']))
                
    return {
        "addresses": addresses,
        "total_balance": str(total)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/wallet/info', methods=['GET'])
def get_wallet_info():
    wif = request.args.get('wif')
    if not wif: return jsonify({'success': False, 'error': 'Thiếu WIF'}), 400
        
    try:
        info = get_total_balance(wif)
        # Tìm lịch sử giao dịch liên quan đến WIF này
        history = [tx for tx in TRANSACTION_HISTORY if tx['sender_wif'] == wif]
        
        return jsonify({
            'success': True,
            'data': info,
            'history': history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wallet/new', methods=['GET'])
def generate_new_wallet():
    try:
        from bitcoinutils.keys import PrivateKey
        priv = PrivateKey()
        return jsonify({
            'success': True,
            'wif': priv.to_wif()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transfer', methods=['POST'])
def transfer_coin():
    data = request.json
    sender_wif = data.get('sender_wif')
    recipient_address = data.get('recipient_address')
    amount_str = data.get('amount', '0')
    absolute_fee_str = data.get('absolute_fee') # Đổi sang nhận phí bằng BTC
    
    try:
        if not sender_wif or not recipient_address:
            raise ValueError("Thiếu thông tin.")
            
        target_amount = Decimal(amount_str)
        absolute_fee = Decimal(absolute_fee_str) if absolute_fee_str else None
        
        try:
            rec_addr = P2wpkhAddress(recipient_address)
            rec_script = rec_addr.to_script_pub_key()
        except:
            rec_addr = P2pkhAddress(recipient_address)
            rec_script = rec_addr.to_script_pub_key()
        
        # Build TX với tùy chỉnh phí thợ đào (BTC)
        signed_tx, dynamic_fee, selected_utxos = build_and_sign_tx(
            sender_wif=sender_wif,
            receiver_pub_script=rec_script,
            target_amount=target_amount,
            absolute_fee=absolute_fee
        )
        
        for u in selected_utxos:
            LOCKED_UTXOS.add(f"{u['txid']}:{u['vout']}")
            
        hex_tx = signed_tx.serialize()
        txid = proxy.sendrawtransaction(hex_tx)
        
        # Ghi vào Sổ cái
        TRANSACTION_HISTORY.append({
            "txid": txid,
            "sender_wif": sender_wif,
            "recipient": recipient_address,
            "amount": str(target_amount),
            "fee": str(dynamic_fee),
            "status": "Mempool",
            "time": time.strftime("%H:%M:%S")
        })
        save_history(TRANSACTION_HISTORY)
        
        return jsonify({
            'success': True,
            'txid': txid,
            'fee': str(dynamic_fee),
            'message': "Phát sóng thành công!"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/mine', methods=['POST'])
def mine_block():
    """Thợ đào Đóng Block (Bao gồm Phân tích Block theo Sơ đồ)"""
    try:
        miner_priv = PrivateKey(MINER_WIF)
        miner_addr = miner_priv.get_public_key().get_segwit_address().to_string()
        
        # 1. Gọi lệnh đào block
        proxy.generatetoaddress(1, miner_addr)
        
        # 2. Phân tích block vừa đào để lấy Hash và phần thưởng
        best_block_hash = proxy.getbestblockhash()
        block_info = proxy.getblock(best_block_hash)
        coinbase_txid = block_info['tx'][0]
        coinbase_tx = proxy.getrawtransaction(coinbase_txid, True)
        miner_reward = coinbase_tx['vout'][0]['value']
        
        # 3. Gỡ khóa UTXO và cập nhật trạng thái Sổ cái
        LOCKED_UTXOS.clear()
        for tx in TRANSACTION_HISTORY:
            if tx['status'] == 'Mempool':
                tx['status'] = 'Confirmed'
        save_history(TRANSACTION_HISTORY)
                
        return jsonify({
            'success': True,
            'message': "Đóng Block Thành Công",
            'block_hash': best_block_hash,
            'height': block_info['height'],
            'reward': str(miner_reward)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
