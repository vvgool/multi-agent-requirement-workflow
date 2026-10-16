import unittest

from parity import is_even


class ParityTests(unittest.TestCase):
    def test_integer_parity_and_boolean_result(self):
        for value, expected in [(0, True), (2, True), (-2, True),
                                (1, False), (-1, False),
                                (10 ** 100, True), (10 ** 100 + 1, False)]:
            with self.subTest(value=value):
                actual = is_even(value)
                self.assertIs(type(actual), bool)
                self.assertIs(actual, expected)

    def test_rejects_non_integer_types_without_conversion(self):
        for value in [True, False, 1.0, "2", None]:
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    is_even(value)


if __name__ == "__main__":
    unittest.main()
