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

HISTORY_FILE = 'data/history.json'

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
    balances = {}
    
    for addr_type, addr in addresses.items():
        addr_total = Decimal('0')
        data = get_utxos_by_address(addr)
        for u in data.get('unspents', []):
            utxo_id = f"{u['txid']}:{u['vout']}"
            if utxo_id not in LOCKED_UTXOS:
                addr_total += Decimal(str(u['amount']))
        balances[addr_type] = str(addr_total)
        total += addr_total
                
    return {
        "addresses": addresses,
        "balances": balances,
        "total_balance": str(total)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/wallet/info', methods=['GET'])
def get_wallet_info():
    wif = request.args.get('wif')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    if not wif: return jsonify({'success': False, 'error': 'Thiếu WIF'}), 400
        
    try:
        info = get_total_balance(wif)
        # Lấy danh sách địa chỉ của ví này để so sánh
        my_addresses = list(info['addresses'].values())
        
        # Tìm lịch sử giao dịch liên quan đến WIF này (gửi đi HOẶC nhận về)
        history = [tx for tx in TRANSACTION_HISTORY if (tx['sender_wif'] == wif) or (tx['recipient'] in my_addresses)]
        # Đảo ngược để giao dịch mới nhất lên đầu
        history.reverse()
        
        # Phân trang
        total_items = len(history)
        start = (page - 1) * limit
        end = start + limit
        paginated_history = history[start:end]
        
        return jsonify({
            'success': True,
            'data': info,
            'history': paginated_history,
            'total_items': total_items,
            'total_pages': (total_items + limit - 1) // limit,
            'current_page': page
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

@app.route('/api/transaction/build', methods=['POST'])
def build_transaction():
    """BƯỚC 1: Xây dựng Giao dịch (Không phát sóng)"""
    data = request.json
    sender_wif = data.get('sender_wif')
    recipient_address = data.get('recipient_address')
    amount_str = data.get('amount', '0')
    absolute_fee_str = data.get('absolute_fee')
    op_return_msg = data.get('op_return_msg')
    
    try:
        if not sender_wif or not recipient_address:
            raise ValueError("Thiếu thông tin.")
            
        target_amount = Decimal(amount_str)
        absolute_fee = Decimal(absolute_fee_str) if absolute_fee_str else None
        
        # Hỗ trợ parse 4 loại địa chỉ
        rec_script = None
        try:
            rec_script = P2wpkhAddress(recipient_address).to_script_pub_key()
        except: pass
        if not rec_script:
            try:
                rec_script = P2pkhAddress(recipient_address).to_script_pub_key()
            except: pass
        if not rec_script:
            try:
                rec_script = P2shAddress(recipient_address).to_script_pub_key()
            except: pass
        if not rec_script:
            try:
                rec_script = P2trAddress(recipient_address).to_script_pub_key()
            except: pass
            
        if not rec_script:
            raise ValueError("Địa chỉ người nhận không hợp lệ hoặc không được hỗ trợ.")
        
        # Build TX (Bốc UTXO và Ký nhưng KHÔNG ném lên mạng)
        signed_tx, dynamic_fee, selected_utxos = build_and_sign_tx(
            sender_wif=sender_wif,
            receiver_pub_script=rec_script,
            target_amount=target_amount,
            absolute_fee=absolute_fee,
            locked_utxos=LOCKED_UTXOS,
            op_return_msg=op_return_msg
        )
        
        hex_tx = signed_tx.serialize()
        
        # Gửi dữ liệu chi tiết cho UI để phân tích
        return jsonify({
            'success': True,
            'fee': float(dynamic_fee),
            'hex': hex_tx,
            'selected_utxos': selected_utxos,
            'target_amount': float(target_amount)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/transaction/broadcast', methods=['POST'])
def broadcast_transaction():
    """BƯỚC 2: Phát sóng Raw Hex lên Mempool"""
    data = request.json
    hex_tx = data.get('hex')
    sender_wif = data.get('sender_wif')
    recipient_address = data.get('recipient_address')
    amount = data.get('amount')
    fee = data.get('fee')
    selected_utxos = data.get('selected_utxos', [])
    
    try:
        if not hex_tx:
            raise ValueError("Thiếu mã Raw Hex.")
            
        # Phát sóng lên mạng
        txid = proxy.sendrawtransaction(hex_tx)
        
        # Thành công thì mới Khóa UTXO (tránh double-spend lúc đang suy nghĩ ở giao diện)
        for u in selected_utxos:
            LOCKED_UTXOS.add(f"{u['txid']}:{u['vout']}")
        
        # Ghi vào Sổ cái
        TRANSACTION_HISTORY.append({
            "txid": txid,
            "sender_wif": sender_wif,
            "recipient": recipient_address,
            "amount": float(amount),
            "fee": float(fee),
            "status": "Mempool",
            "time": time.strftime("%H:%M:%S")
        })
        save_history(TRANSACTION_HISTORY)
        
        return jsonify({
            'success': True,
            'txid': txid
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
            'reward': str(miner_reward),
            'tx_count': len(block_info['tx']) - 1
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transaction/<txid>', methods=['GET'])
def get_transaction_details(txid):
    """API Lấy chi tiết giao dịch từ Node Bitcoin"""
    try:
        # True để decode raw hex thành JSON chi tiết
        tx_info = proxy.getrawtransaction(txid, True)
        return jsonify({
            'success': True,
            'data': tx_info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404
@app.route('/api/miner/mempool', methods=['GET'])
def get_mempool():
    """Lấy danh sách các giao dịch đang chờ trong Mempool"""
    try:
        raw_mempool = proxy.getrawmempool(True)
        txs = []
        total_fee = Decimal('0')
        total_vsize = 0
        
        for txid, details in raw_mempool.items():
            fee = details.get('fee', 0)
            vsize = details.get('vsize', 0)
            
            total_fee += Decimal(str(fee))
            total_vsize += vsize
            
            txs.append({
                'txid': txid,
                'fee': fee,
                'vsize': vsize,
                'time': details.get('time', 0)
            })
            
        # Sắp xếp theo phí giảm dần (ưu tiên đóng block)
        txs.sort(key=lambda x: x['fee'], reverse=True)
        
        return jsonify({
            'success': True,
            'txs': txs,
            'total_fee': float(total_fee),
            'total_vsize': total_vsize,
            'tx_count': len(txs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/miner/info', methods=['GET'])
def get_miner_info():
    """Lấy thông tin ví của Thợ đào"""
    try:
        if not MINER_WIF:
            return jsonify({'success': False, 'error': 'Thiếu MINER_WIF trong .env'}), 400
            
        info = get_total_balance(MINER_WIF)
        
        miner_priv = PrivateKey(MINER_WIF)
        # Thông thường thợ đào nhận qua Native Segwit
        miner_addr = miner_priv.get_public_key().get_segwit_address().to_string()
        
        return jsonify({
            'success': True,
            'address': miner_addr,
            'balance': info['total_balance']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
