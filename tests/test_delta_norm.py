
# Tests for NK-1 δ-Norm Enforcement

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk1.delta_norm import (
    NormDomainMode,
    compute_delta_norm,
    normalize_weight,
    lcm,
    lcm_list,
    requires_mode_d,
    is_numeric_field
)


class TestNormDomainMode(unittest.TestCase):
    """Tests for NormDomainMode."""
    
    def test_numeric_only_v1(self):
        """Test numeric_only_v1 mode."""
        self.assertEqual(NormDomainMode.NUMERIC_ONLY_V1, "numeric_only.v1")


class TestIsNumericField(unittest.TestCase):
    """Tests for is_numeric_field."""
    
    def test_integer_is_numeric(self):
        """Test integer is numeric."""
        self.assertTrue(is_numeric_field("integer"))
    
    def test_nonneg_is_numeric(self):
        """Test nonneg is numeric."""
        self.assertTrue(is_numeric_field("nonneg"))
    
    def test_rational_is_numeric(self):
        """Test rational is numeric."""
        self.assertTrue(is_numeric_field("rational"))
    
    def test_bool_not_numeric(self):
        """Test bool is not numeric."""
        self.assertFalse(is_numeric_field("bool"))
    
    def test_string_not_numeric(self):
        """Test string is not numeric."""
        self.assertFalse(is_numeric_field("string"))
    
    def test_bytes_not_numeric(self):
        """Test bytes is not numeric."""
        self.assertFalse(is_numeric_field("bytes"))


class TestComputeDeltaNorm(unittest.TestCase):
    """Tests for compute_delta_norm."""
    
    def test_delta_norm_numeric_only(self):
        """Test δ-norm only includes numeric fields."""
        field_defs = {
            "f:balance": {
                "type": "integer",
                "participates_in_delta_norm": True
            },
            "f:name": {
                "type": "string",
                "participates_in_delta_norm": True  # Should be ignored
            }
        }
        
        weights = {"f:balance": (1, 1)}
        
        state_before = {"f:balance": 100, "f:name": "alice"}
        state_after = {"f:balance": 150, "f:name": "bob"}
        
        # Should only compute delta for numeric fields
        delta = compute_delta_norm(state_before, state_after, field_defs, weights)
        
        # Delta is 50 (150-100) with weight 1
        self.assertEqual(delta[0], 50)
    
    def test_delta_norm_weighted(self):
        """Test δ-norm with weights."""
        field_defs = {
            "f:balance": {
                "type": "integer",
                "participates_in_delta_norm": True
            }
        }
        
        weights = {"f:balance": (2, 1)}  # Weight = 2
        
        state_before = {"f:balance": 100}
        state_after = {"f:balance": 150}
        
        delta = compute_delta_norm(state_before, state_after, field_defs, weights)
        
        # Delta is (150-100) * 2 = 100
        self.assertEqual(delta[0], 100)
    
    def test_delta_norm_non_participating(self):
        """Test δ-norm excludes non-participating fields."""
        field_defs = {
            "f:balance": {
                "type": "integer",
                "participates_in_delta_norm": False  # Does not participate
            }
        }
        
        weights = {"f:balance": (1, 1)}
        
        state_before = {"f:balance": 100}
        state_after = {"f:balance": 150}
        
        delta = compute_delta_norm(state_before, state_after, field_defs, weights)
        
        # Should be zero since field doesn't participate
        self.assertEqual(delta, (0, 1))
    
    def test_delta_norm_multiple_fields(self):
        """Test δ-norm with multiple fields."""
        field_defs = {
            "f:balance": {
                "type": "integer",
                "participates_in_delta_norm": True
            },
            "f:version": {
                "type": "integer",
                "participates_in_delta_norm": True
            }
        }
        
        weights = {
            "f:balance": (1, 1),
            "f:version": (1, 1)
        }
        
        state_before = {"f:balance": 100, "f:version": 5}
        state_after = {"f:balance": 150, "f:version": 6}
        
        delta = compute_delta_norm(state_before, state_after, field_defs, weights)
        
        # Delta is (50 + 1) = 51
        self.assertEqual(delta[0], 51)


class TestNormalizeWeight(unittest.TestCase):
    """Tests for normalize_weight."""
    
    def test_reduce_fraction(self):
        """Test weight reduction."""
        self.assertEqual(normalize_weight((2, 4)), (1, 2))
        self.assertEqual(normalize_weight((3, 6)), (1, 2))
        self.assertEqual(normalize_weight((4, 2)), (2, 1))
    
    def test_zero_weight(self):
        """Test zero weight."""
        self.assertEqual(normalize_weight((0, 5)), (0, 1))


class TestLCM(unittest.TestCase):
    """Tests for LCM functions."""
    
    def test_lcm_basic(self):
        """Test basic LCM."""
        self.assertEqual(lcm(2, 3), 6)
        self.assertEqual(lcm(4, 6), 12)
        self.assertEqual(lcm(5, 5), 5)
    
    def test_lcm_with_zero(self):
        """Test LCM with zero."""
        self.assertEqual(lcm(0, 5), 0)
        self.assertEqual(lcm(5, 0), 0)
    
    def test_lcm_list_basic(self):
        """Test LCM of list."""
        self.assertEqual(lcm_list([2, 3, 4]), 12)
    
    def test_lcm_list_empty(self):
        """Test LCM of empty list."""
        self.assertEqual(lcm_list([]), 1)


class TestRequiresModeD(unittest.TestCase):
    """Tests for requires_mode_d."""
    
    def test_requires_mode_d_numeric_only(self):
        """Test Mode D not required for numeric-only operations."""
        field_defs = {
            "f:balance": {
                "type": "integer",
            }
        }
        
        ops = [
            {"writes": [{"field_id": "f:balance", "value": 200}]}
        ]
        
        self.assertFalse(requires_mode_d(ops, field_defs))
    
    def test_requires_mode_d_with_string(self):
        """Test Mode D required for string writes."""
        field_defs = {
            "f:balance": {
                "type": "integer",
            },
            "f:name": {
                "type": "string",
            }
        }
        
        ops = [
            {"writes": [{"field_id": "f:name", "value": "alice"}]}
        ]
        
        self.assertTrue(requires_mode_d(ops, field_defs))
    
    def test_requires_mode_d_mixed(self):
        """Test Mode D required for mixed operations."""
        field_defs = {
            "f:balance": {
                "type": "integer",
            },
            "f:name": {
                "type": "string",
            }
        }
        
        ops = [
            {"writes": [
                {"field_id": "f:balance", "value": 200},
                {"field_id": "f:name", "value": "alice"}
            ]}
        ]
        
        self.assertTrue(requires_mode_d(ops, field_defs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
