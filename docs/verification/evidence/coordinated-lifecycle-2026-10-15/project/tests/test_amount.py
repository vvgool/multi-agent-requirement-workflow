import unittest

from amount import format_amount


class AmountTests(unittest.TestCase):
    def test_ac001_examples(self):
        for cents, expected in [(0, "0.00"), (1, "0.01"), (105, "1.05"), (10000, "100.00")]:
            with self.subTest(cents=cents):
                self.assertEqual(format_amount(cents), expected)

    def test_ac002_boundaries(self):
        for cents, expected in [(99, "0.99"), (100, "1.00"), (101, "1.01"), (123456789, "1234567.89")]:
            with self.subTest(cents=cents):
                self.assertEqual(format_amount(cents), expected)

    def test_ac003_precision(self):
        self.assertEqual(format_amount(9007199254740993), "90071992547409.93")
        self.assertEqual(format_amount(10**100 + 1), "1" + "0" * 98 + ".01")

    def test_ac004_negative_integers(self):
        for value in [-1, -100, -(10**100)]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    format_amount(value)

    def test_ac005_non_integer_inputs(self):
        for value in ["105", 1.05, 1.0, -1.0, None, True, False]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    format_amount(value)

    def test_ac006_imported_function(self):
        self.assertTrue(callable(format_amount))
        self.assertIsInstance(format_amount(105), str)

    def test_small_range_regression(self):
        for cents in range(10001):
            expected_digits = str(cents).zfill(3)
            self.assertEqual(format_amount(cents), expected_digits[:-2] + "." + expected_digits[-2:])

    def test_chunk_boundaries_and_very_large_integer(self):
        self.assertEqual(format_amount(10**11 - 1), "999999999.99")
        self.assertEqual(format_amount(10**11), "1000000000.00")
        self.assertEqual(format_amount(10**11 + 1), "1000000000.01")
        self.assertEqual(format_amount(10**5000 + 1), "1" + "0" * 4998 + ".01")
