import sys, unittest
sys.path.insert(0, '/var/folders/p7/6lh96zx51qz0ksknm0qj5v3r0000gp/T/development-skill-check-faz2h1cd/consumer/project')
from shipping import shipping_fee
from checkout import checkout_total
class Acceptance(unittest.TestCase):
    def test_ac1_nonnegative_fee(self):
        for n in [*range(0, 30001), 10**12, 10**100]:
            self.assertEqual(shipping_fee(n), 1000 if n < 10000 else 0, n)
    def test_ac2_negative(self):
        for n in [-1,-9999,-10000,-10001,-10**12,-10**100]:
            with self.subTest(n=n), self.assertRaises(ValueError): shipping_fee(n)
    def test_ac3_checkout_integration(self):
        for n in [*range(0, 30001),10**12,10**100]:
            self.assertEqual(checkout_total(n), n + (1000 if n < 10000 else 0), n)
    def test_negative_propagation(self):
        with self.assertRaises(ValueError): checkout_total(-1)
if __name__ == '__main__': unittest.main(verbosity=2)
