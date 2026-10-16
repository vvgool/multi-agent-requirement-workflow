import sys, pathlib, unittest
sys.dont_write_bytecode=True
project=pathlib.Path(__file__).resolve().parents[6]/'project'
sys.path.insert(0,str(project))
from shipping import shipping_fee
from checkout import checkout_total
class Acceptance(unittest.TestCase):
    def test_ac1_range(self):
        for value in list(range(20001))+[10**12]:
            with self.subTest(subtotal=value):
                self.assertEqual(shipping_fee(value),1000 if value<10000 else 0)
    def test_ac2_negative(self):
        for value in [-1,-10000,-10**12]:
            with self.subTest(subtotal=value):
                with self.assertRaises(ValueError): shipping_fee(value)
    def test_ac3_actual_checkout(self):
        for value in [0,1,9999,10000,10001,10**12]:
            with self.subTest(subtotal=value):
                self.assertEqual(checkout_total(value),value+(1000 if value<10000 else 0))
    def test_checkout_negative_propagation(self):
        for value in [-1,-10000,-10**12]:
            with self.subTest(subtotal=value):
                with self.assertRaises(ValueError): checkout_total(value)
if __name__=='__main__': unittest.main(verbosity=2)
