import sys
import os
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from tx_builder import estimate_tx_fee

class TestEstimateFee(unittest.TestCase):
    def test_estimate_fee_legacy(self):
        # 1 input (148 bytes), 2 outputs (34*2 bytes), base 10 bytes = 226 bytes
        # Fee rate = 10 sat/byte => 2260 satoshi => 0.0000226 BTC
        fee = estimate_tx_fee("legacy", 1, 2, 10)
        self.assertEqual(fee, Decimal("0.0000226"))
        
    def test_estimate_fee_taproot(self):
        # 1 input (57.5 bytes), 2 outputs (34*2 bytes), base 10 bytes = 135.5 bytes
        # Fee rate = 10 sat/byte => 1355 satoshi => 0.00001355 BTC
        fee = estimate_tx_fee("taproot", 1, 2, 10)
        self.assertEqual(fee, Decimal("0.00001355"))

if __name__ == '__main__':
    unittest.main()
