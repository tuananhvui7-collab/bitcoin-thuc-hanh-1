import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from tx_builder import derive_all_address_types

class TestDeriveAddresses(unittest.TestCase):
    def test_derive_all_address_types(self):
        # WIF cố định của Alice
        wif = "cSmKSQgPLqn9jSt89KjbhTiBpT7qK4jWrdQnmgMzHPuhZvVbp82V"
        
        addresses = derive_all_address_types(wif)
        
        # Kiểm tra xem có đủ 4 loại địa chỉ không
        self.assertIn("legacy", addresses)
        self.assertIn("nested_segwit", addresses)
        self.assertIn("native_segwit", addresses)
        self.assertIn("taproot", addresses)
        
        # Kiểm tra định dạng (Prefix) của từng loại trên mạng Regtest
        self.assertTrue(addresses["legacy"].startswith(("m", "n")))
        self.assertTrue(addresses["nested_segwit"].startswith("2"))
        self.assertTrue(addresses["native_segwit"].startswith("bcrt1q"))
        self.assertTrue(addresses["taproot"].startswith("bcrt1p"))

if __name__ == '__main__':
    unittest.main()
