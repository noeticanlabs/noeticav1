# CK-0 Unit Tests: Curvature Matrix

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ck0.curvature import CurvatureMatrix, compute_curvature_bound, compute_nec_closure
from fractions import Fraction


class TestCurvatureMatrixBasics(unittest.TestCase):
    """Basic CurvatureMatrix tests."""
    
    def test_create_zero_matrix(self):
        m = CurvatureMatrix.create_zero(3)
        self.assertEqual(m.size(), 3)
        self.assertEqual(m.get(0, 0), Fraction(0))
    
    def test_create_identity(self):
        m = CurvatureMatrix.create_identity(3, Fraction(1))
        self.assertEqual(m.get(0, 0), Fraction(1))
        self.assertEqual(m.get(1, 1), Fraction(1))
        self.assertEqual(m.get(0, 1), Fraction(0))
    
    def test_set_and_get(self):
        m = CurvatureMatrix.create_zero(2)
        m.set(0, 1, Fraction(1, 2))
        self.assertEqual(m.get(0, 1), Fraction(1, 2))
        self.assertEqual(m.get(1, 0), Fraction(1, 2))  # Symmetric


class TestCurvatureMatrixRationalReduction(unittest.TestCase):
    """Test rational reduction."""
    
    def test_rational_reduction(self):
        m = CurvatureMatrix.create_zero(1)
        m.set(0, 0, Fraction(2, 4))  # Should reduce to 1/2
        self.assertEqual(m.get(0, 0), Fraction(1, 2))
    
    def test_negative_reduction(self):
        m = CurvatureMatrix.create_zero(1)
        m.set(0, 0, Fraction(-2, 4))  # Should reduce to -1/2
        self.assertEqual(m.get(0, 0), Fraction(-1, 2))


class TestCurvatureMatrixDigest(unittest.TestCase):
    """Test matrix digest."""
    
    def test_compute_digest(self):
        m = CurvatureMatrix.create_identity(2)
        digest = m.compute_digest()
        self.assertTrue(digest.startswith("h:"))
        self.assertEqual(len(digest), 66)  # "h:" + 64 hex chars
    
    def test_digest_cached(self):
        m = CurvatureMatrix.create_identity(2)
        d1 = m.compute_digest()
        d2 = m.compute_digest()
        self.assertEqual(d1, d2)


class TestCurvatureCanonicalBytes(unittest.TestCase):
    """Test canonical bytes."""
    
    def test_canonical_bytes(self):
        m = CurvatureMatrix.create_identity(2)
        cb = m.canonical_bytes()
        self.assertIsInstance(cb, bytes)
        self.assertTrue(cb.startswith(b"matrix_v1:"))


class TestComputeCurvatureBound(unittest.TestCase):
    """Test curvature bound computation."""
    
    def test_simple_bound(self):
        bound = compute_curvature_bound(
            Fraction(1), Fraction(1),
            Fraction(1), Fraction(1), Fraction(1)
        )
        # |1 * 1 * 1| = 1
        self.assertEqual(bound, Fraction(1))


class TestNECClosure(unittest.TestCase):
    """Test NEC closure computation."""
    
    def test_empty_residuals(self):
        m = compute_nec_closure([], CurvatureMatrix.create_zero(0))
        self.assertEqual(m.size(), 0)
    
    def test_simple_closure(self):
        residuals = [Fraction(1), Fraction(1)]
        hessian = CurvatureMatrix.create_zero(2)
        hessian.set(0, 0, Fraction(1))
        hessian.set(1, 1, Fraction(1))
        hessian.set(0, 1, Fraction(1))
        
        m = compute_nec_closure(residuals, hessian)
        self.assertEqual(m.size(), 2)


class TestValidateCurvatureMatrix(unittest.TestCase):
    """Test curvature matrix validation."""
    
    def test_valid_matrix(self):
        from ck0.curvature import validate_curvature_matrix
        m = CurvatureMatrix.create_identity(2)
        is_valid, msg = validate_curvature_matrix(m, [Fraction(1), Fraction(1)])
        self.assertTrue(is_valid)
    
    def test_size_mismatch(self):
        from ck0.curvature import validate_curvature_matrix
        m = CurvatureMatrix.create_identity(2)
        is_valid, msg = validate_curvature_matrix(m, [Fraction(1)])
        self.assertFalse(is_valid)


if __name__ == '__main__':
    unittest.main()
