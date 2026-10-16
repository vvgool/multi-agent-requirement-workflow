import argparse
import sys
import unittest
from pathlib import Path

parser = argparse.ArgumentParser(description="Independent shipping fixture acceptance")
parser.add_argument("--project", required=True, type=Path)
args = parser.parse_args()
sys.dont_write_bytecode = True
sys.path.insert(0, str(args.project.resolve()))
from shipping import shipping_fee
from checkout import checkout_total


class IndependentAcceptance(unittest.TestCase):
    def test_ac1_full_integer_range_and_large(self):
        for n in list(range(20001)) + [10**12]:
            self.assertEqual(shipping_fee(n), 1000 if n < 10000 else 0, n)

    def test_ac2_negative_integers(self):
        for n in [-1, -9999, -10000, -10**12]:
            with self.assertRaises(ValueError):
                shipping_fee(n)

    def test_ac3_real_checkout_call_chain(self):
        for n in list(range(20001)) + [10**12]:
            self.assertEqual(checkout_total(n), n + (1000 if n < 10000 else 0), n)

    def test_checkout_negative_regression(self):
        for n in [-1, -10000, -10**12]:
            with self.assertRaises(ValueError):
                checkout_total(n)

    def test_corrected_old_case_boundary(self):
        self.assertEqual(shipping_fee(10000), 0)
        self.assertEqual(checkout_total(10000), 10000)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(IndependentAcceptance)
    )
    print("Boundary readback: shipping_fee(10000)=" + str(shipping_fee(10000))
          + "; checkout_total(10000)=" + str(checkout_total(10000)))
    sys.exit(0 if result.wasSuccessful() else 1)
