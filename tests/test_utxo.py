import sys
import os
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from tx_builder import select_utxos

class TestUTXOSelection(unittest.TestCase):
    def setUp(self):
        # Tạo danh sách UTXO giả lập để test
        self.mock_utxos = [
            {"txid": "1111", "vout": 0, "amount": 0.5},
            {"txid": "2222", "vout": 1, "amount": 2.0},
            {"txid": "3333", "vout": 0, "amount": 10.0},
            {"txid": "4444", "vout": 2, "amount": 50.0},
        ]
        
    def test_select_utxos_success(self):
        # Cần gửi 11 BTC. Thuật toán Largest-first sẽ nhặt tờ 50 BTC đầu tiên.
        target = Decimal("11.0")
        
        selected, total = select_utxos(self.mock_utxos, target)
        
        # Chỉ cần 1 tờ 50 BTC là đủ trả
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["txid"], "4444")
        self.assertEqual(total, Decimal("50.0"))
        
    def test_select_utxos_multiple(self):
        # Cần gửi 55 BTC. Thuật toán sẽ nhặt tờ 50 BTC, rồi nhặt tiếp tờ 10 BTC.
        target = Decimal("55.0")
        
        selected, total = select_utxos(self.mock_utxos, target)
        
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]["txid"], "4444") # 50
        self.assertEqual(selected[1]["txid"], "3333") # 10
        self.assertEqual(total, Decimal("60.0"))
        
    def test_select_utxos_insufficient_funds(self):
        # Cần gửi 100 BTC nhưng tổng ví chỉ có 62.5 BTC
        target = Decimal("100.0")
        
        with self.assertRaises(ValueError) as context:
            select_utxos(self.mock_utxos, target)
            
        self.assertTrue("không đủ tiền" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
