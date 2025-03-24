import unittest
from decimal import Decimal
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from lambda_functions.getInventory import decimal_to_str

class TestDecimalConversion(unittest.TestCase):
    def test_decimal_conversion(self):
        decimal_value = Decimal('10.99')
        self.assertEqual(decimal_to_str(decimal_value), '10.99')

    def test_dict_conversion(self):
        test_dict = {
            'price': Decimal('10.99'),
            'quantity': 5,
            'name': 'test'
        }
        expected = {
            'price': '10.99',
            'quantity': 5,
            'name': 'test'
        }
        self.assertEqual(decimal_to_str(test_dict), expected)

    def test_list_conversion(self):
        test_list = [Decimal('10.99'), Decimal('20.50'), 'test', 42]
        expected = ['10.99', '20.50', 'test', 42]
        self.assertEqual(decimal_to_str(test_list), expected)

    def test_nested_structure(self):
        test_data = {
            'items': [
                {'price': Decimal('10.99'), 'quantity': 2},
                {'price': Decimal('20.50'), 'quantity': 1}
            ],
            'total': Decimal('42.48')
        }
        expected = {
            'items': [
                {'price': '10.99', 'quantity': 2},
                {'price': '20.50', 'quantity': 1}
            ],
            'total': '42.48'
        }
        self.assertEqual(decimal_to_str(test_data), expected)

    def test_non_decimal_values(self):
        test_values = [
            42,
            "string",
            True,
            None,
            [1, 2, 3],
            {'a': 1, 'b': 2}
        ]
        for value in test_values:
            self.assertEqual(decimal_to_str(value), value)

if __name__ == '__main__':
    unittest.main()