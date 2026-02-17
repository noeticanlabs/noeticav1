# CK-0 Unit Tests: DebtUnit

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ck0.debtunit import DebtUnit, ZERO, ONE
from fractions import Fraction


class TestDebtUnitBasics(unittest.TestCase):
    """Basic DebtUnit tests."""
    
    def test_create_from_int(self):
        d = DebtUnit(5)
        self.assertEqual(d.value, 5)
    
    def test_create_from_debtunit(self):
        d1 = DebtUnit(10)
        d2 = DebtUnit(d1)
        self.assertEqual(d2.value, 10)
    
    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            DebtUnit(-1)
    
    def test_non_int_raises(self):
        with self.assertRaises(TypeError):
            DebtUnit(3.14)


class TestDebtUnitArithmetic(unittest.TestCase):
    """Arithmetic operation tests."""
    
    def test_addition(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(3)
        result = d1 + d2
        self.assertEqual(result.value, 8)
    
    def test_subtraction(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(3)
        result = d1 - d2
        self.assertEqual(result.value, 2)
    
    def test_subtraction_negative_raises(self):
        d1 = DebtUnit(3)
        d2 = DebtUnit(5)
        with self.assertRaises(ValueError):
            result = d1 - d2
    
    def test_multiplication(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(3)
        result = d1 * d2
        self.assertEqual(result.value, 15)
    
    def test_division(self):
        d1 = DebtUnit(10)
        d2 = DebtUnit(2)
        result = d1 / d2
        self.assertEqual(result, Fraction(5))
    
    def test_zero_division_raises(self):
        d1 = DebtUnit(10)
        d2 = DebtUnit(0)
        with self.assertRaises(ZeroDivisionError):
            result = d1 / d2


class TestDebtUnitComparison(unittest.TestCase):
    """Comparison operation tests."""
    
    def test_equality(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(5)
        self.assertEqual(d1, d2)
    
    def test_inequality(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(3)
        self.assertNotEqual(d1, d2)
    
    def test_less_than(self):
        d1 = DebtUnit(3)
        d2 = DebtUnit(5)
        self.assertTrue(d1 < d2)
    
    def test_greater_than(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(3)
        self.assertTrue(d1 > d2)
    
    def test_less_equal(self):
        d1 = DebtUnit(3)
        d2 = DebtUnit(3)
        self.assertTrue(d1 <= d2)
    
    def test_greater_equal(self):
        d1 = DebtUnit(5)
        d2 = DebtUnit(3)
        self.assertTrue(d1 >= d2)


class TestDebtUnitFromFraction(unittest.TestCase):
    """Test DebtUnit.from_fraction with half-even rounding."""
    
    def test_simple_fraction(self):
        frac = Fraction(1, 2)
        result = DebtUnit.from_fraction(frac, 1000)
        self.assertEqual(result.value, 500)
    
    def test_rounds_up(self):
        # 3.6 * 1000 = 3600, rounds up to 4000 (more than half)
        frac = Fraction(18, 5)
        result = DebtUnit.from_fraction(frac, 1000)
        self.assertEqual(result.value, 4000)
    
    def test_half_even_rounds_down(self):
        # 2.5 * 1000 = 2500, half-even: rounds to even = 2000
        frac = Fraction(5, 2)
        result = DebtUnit.from_fraction(frac, 1000)
        self.assertEqual(result.value, 2000)
    
    def test_half_even_rounds_up(self):
        # 3.5 * 1000 = 3500, half-even: rounds to even = 4000
        frac = Fraction(7, 2)
        result = DebtUnit.from_fraction(frac, 1000)
        self.assertEqual(result.value, 4000)


class TestDebtUnitCanonical(unittest.TestCase):
    """Test canonical byte representation."""
    
    def test_canonical_bytes(self):
        d = DebtUnit(100)
        cb = d.canonical_bytes()
        self.assertIsInstance(cb, bytes)
    
    def test_from_canonical_bytes(self):
        d1 = DebtUnit(100)
        cb = d1.canonical_bytes()
        d2 = DebtUnit.from_canonical_bytes(cb)
        self.assertEqual(d1, d2)


class TestDebtUnitConstants(unittest.TestCase):
    """Test module constants."""
    
    def test_zero(self):
        self.assertEqual(ZERO.value, 0)
    
    def test_one(self):
        self.assertEqual(ONE.value, 1)


if __name__ == '__main__':
    unittest.main()
