# Tests for NK-1 Curvature Matrix Registry

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk1.curvature_matrix import (
    CurvatureMatrix,
    CurvatureMatrixRegistry,
    CANON_MATRIX_ID,
    reduce_fraction
)


class TestReduceFraction(unittest.TestCase):
    """Tests for reduce_fraction helper."""
    
    def test_reduce_positive(self):
        """Reduce positive fraction."""
        self.assertEqual(reduce_fraction(2, 4), (1, 2))
        self.assertEqual(reduce_fraction(6, 8), (3, 4))
    
    def test_reduce_negative(self):
        """Reduce negative fraction."""
        self.assertEqual(reduce_fraction(-2, 4), (-1, 2))
        self.assertEqual(reduce_fraction(2, -4), (-1, 2))
    
    def test_zero_numerator(self):
        """Zero numerator."""
        self.assertEqual(reduce_fraction(0, 5), (0, 1))
    
    def test_negative_denominator(self):
        """Negative denominator moves to numerator."""
        self.assertEqual(reduce_fraction(1, -2), (-1, 2))


class TestCurvatureMatrix(unittest.TestCase):
    """Tests for CurvatureMatrix."""
    
    def setUp(self):
        self.matrix = CurvatureMatrix(dimension=3)
    
    def test_create_matrix(self):
        """Create matrix with dimension."""
        self.assertEqual(self.matrix.dimension, 3)
        self.assertEqual(len(self.matrix.entries), 0)
    
    def test_set_entry_upper_triangle(self):
        """Set entry stores in upper triangle."""
        self.matrix.set_entry(1, 0, 1, 2)  # Set (0,1)
        self.assertIn((0, 1), self.matrix.entries)
        self.assertNotIn((1, 0), self.matrix.entries)
    
    def test_symmetry_fill(self):
        """Symmetry fill: M_ij = M_ji."""
        self.matrix.set_entry(0, 1, 1, 2)
        self.assertEqual(self.matrix.get_entry(0, 1), (1, 2))
        self.assertEqual(self.matrix.get_entry(1, 0), (1, 2))
    
    def test_missing_entry_defaults_zero(self):
        """Missing entry defaults to 0."""
        self.assertEqual(self.matrix.get_entry(1, 2), (0, 1))
    
    def test_reduce_fraction_on_set(self):
        """Fraction is reduced on set."""
        self.matrix.set_entry(0, 0, 2, 4)
        self.assertEqual(self.matrix.entries[(0, 0)], (1, 2))
    
    def test_invalid_index_negative(self):
        """Negative index raises error."""
        with self.assertRaises(ValueError):
            self.matrix.set_entry(-1, 0, 1)
    
    def test_invalid_index_out_of_bounds(self):
        """Out of bounds index raises error."""
        with self.assertRaises(ValueError):
            self.matrix.set_entry(3, 0, 1)
    
    def test_to_canonical_bytes(self):
        """Serialize to canonical bytes."""
        self.matrix.set_entry(0, 0, 1)
        self.matrix.set_entry(0, 1, 1, 2)
        
        canon_bytes = self.matrix.to_canonical_bytes()
        self.assertIsInstance(canon_bytes, bytes)
        
        # Verify it's valid JSON
        import json
        parsed = json.loads(canon_bytes.decode('utf-8'))
        self.assertEqual(parsed["canon_id"], CANON_MATRIX_ID)
        self.assertEqual(parsed["dimension"], 3)
    
    def test_canonical_bytes_sorted(self):
        """Canonical bytes have sorted entries."""
        self.matrix.set_entry(2, 0, 1)  # Will be stored as (0,2)
        self.matrix.set_entry(0, 1, 1, 2)
        
        canon_bytes = self.matrix.to_canonical_bytes()
        import json
        parsed = json.loads(canon_bytes.decode('utf-8'))
        
        # Entries should be sorted by (i, j)
        entries = parsed["entries"]
        self.assertEqual(entries[0]["i"], 0)
        self.assertEqual(entries[0]["j"], 1)
        self.assertEqual(entries[1]["i"], 0)
        self.assertEqual(entries[1]["j"], 2)
    
    def test_compute_digest(self):
        """Compute digest."""
        self.matrix.set_entry(0, 0, 1)
        digest = self.matrix.compute_digest()
        
        self.assertTrue(digest.startswith('h:'))
        self.assertEqual(len(digest), 2 + 64)  # h: + sha3_256 hex
    
    def test_digest_cached(self):
        """Digest is cached."""
        self.matrix.set_entry(0, 0, 1)
        d1 = self.matrix.compute_digest()
        d2 = self.matrix.compute_digest()
        self.assertEqual(d1, d2)
    
    def test_digest_invalidated_on_change(self):
        """Digest changes when matrix changes."""
        self.matrix.set_entry(0, 0, 1)
        d1 = self.matrix.compute_digest()
        
        self.matrix.set_entry(0, 1, 1)
        d2 = self.matrix.compute_digest()
        
        self.assertNotEqual(d1, d2)
    
    def test_from_canonical_bytes(self):
        """Deserialize from canonical bytes."""
        self.matrix.set_entry(0, 0, 1)
        self.matrix.set_entry(0, 1, 1, 2)
        
        canon_bytes = self.matrix.to_canonical_bytes()
        restored = CurvatureMatrix.from_canonical_bytes(canon_bytes)
        
        self.assertEqual(restored.dimension, 3)
        self.assertEqual(restored.get_entry(0, 0), (1, 1))
        self.assertEqual(restored.get_entry(0, 1), (1, 2))
    
    def test_to_rational_matrix(self):
        """Convert to rational matrix."""
        self.matrix.set_entry(0, 0, 1)
        self.matrix.set_entry(1, 1, 2)
        
        rational = self.matrix.to_rational_matrix()
        
        self.assertEqual(rational[0][0], 1.0)
        self.assertEqual(rational[1][1], 2.0)
        self.assertEqual(rational[0][1], 0.0)


class TestCurvatureMatrixRegistry(unittest.TestCase):
    """Tests for CurvatureMatrixRegistry."""
    
    def setUp(self):
        self.registry = CurvatureMatrixRegistry()
    
    def test_register_matrix(self):
        """Register a matrix."""
        matrix = CurvatureMatrix(dimension=2)
        matrix.set_entry(0, 0, 1)
        
        digest = self.registry.register("test_matrix", matrix)
        
        self.assertIsNotNone(digest)
        self.assertTrue(digest.startswith('h:'))
    
    def test_get_matrix(self):
        """Get matrix by ID."""
        matrix = CurvatureMatrix(dimension=2)
        matrix.set_entry(0, 0, 1)
        
        self.registry.register("test_matrix", matrix)
        retrieved = self.registry.get("test_matrix")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get_entry(0, 0), (1, 1))
    
    def test_get_nonexistent(self):
        """Get nonexistent matrix returns None."""
        result = self.registry.get("nonexistent")
        self.assertIsNone(result)
    
    def test_get_by_digest(self):
        """Get matrix by digest."""
        matrix = CurvatureMatrix(dimension=2)
        matrix.set_entry(0, 0, 1)
        
        digest = self.registry.register("test_matrix", matrix)
        retrieved = self.registry.get_by_digest(digest)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get_entry(0, 0), (1, 1))
    
    def test_latest_digest(self):
        """Get latest registered digest."""
        matrix1 = CurvatureMatrix(dimension=2)
        matrix1.set_entry(0, 0, 1)
        
        matrix2 = CurvatureMatrix(dimension=2)
        matrix2.set_entry(0, 0, 2)
        
        d1 = self.registry.register("m1", matrix1)
        d2 = self.registry.register("m2", matrix2)
        
        self.assertEqual(self.registry.latest_digest(), d2)
        self.assertNotEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
