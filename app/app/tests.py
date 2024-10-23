"""
    Sample tests
"""

from django.test import SimpleTestCase
from app import calculate


class CalculationTests(SimpleTestCase):
    """
        Test the calculation module
    """

    def test_addition(self):
        """
            Test the addition function
        """

        result = calculate.addition(2, 5)
        self.assertEqual(result, 7)

    def test_subtraction(self):
        """
            Test the subtraction function
        """

        result = calculate.subtraction(5, 2)
        self.assertEqual(result, 3)