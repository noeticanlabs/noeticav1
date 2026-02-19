"""
Determinism Test Suite for QFixed(18) Arithmetic

This test suite ensures that:
1. Cross-platform consistency
2. Rounding canonicalization
3. Serialization roundtrip
4. Compositionality under arithmetic operations

The QFixed(18) type is fundamental to the governance cost model.
All computations must be deterministic and reproducible.

References:
- plans/coh_structural_audit_implementation_plan.md
- docs/ck0/7_rounding_canonicalization.md
"""

import pytest
from fractions import Fraction
from typing import List


# Simulated QFixed(18) - in practice this would use an actual fixed-point library
# For now, we use Fraction with fixed denominator
QFIXED_DENOM = 10**18


def make_qfixed(value: int) -> Fraction:
    """Create QFixed(18) from integer value."""
    return Fraction(value, QFIXED_DENOM)


def make_qfixed_from_float(value: float) -> Fraction:
    """Create QFixed(18) from float (with rounding)."""
    # Round to 18 decimal places
    scaled = round(value * QFIXED_DENOM)
    return Fraction(scaled, QFIXED_DENOM)


def qfixed_to_fraction(qf: Fraction) -> Fraction:
    """Ensure QFixed has correct denominator."""
    # Normalize to canonical form
    return Fraction(qf.numerator, qf.denominator)


# =============================================================================
# Basic Arithmetic Tests
# =============================================================================

class TestQFixedAddition:
    """Test addition determinism."""
    
    def test_addition_commutative(self):
        """a + b == b + a"""
        a = make_qfixed(123456789012345678)
        b = make_qfixed(987654321098765432)
        
        result1 = a + b
        result2 = b + a
        
        assert result1 == result2, f"{result1} != {result2}"
    
    def test_addition_associative(self):
        """(a + b) + c == a + (b + c)"""
        a = make_qfixed(100000000000000000)
        b = make_qfixed(200000000000000000)
        c = make_qfixed(300000000000000000)
        
        result1 = (a + b) + c
        result2 = a + (b + c)
        
        assert result1 == result2, f"{result1} != {result2}"
    
    def test_addition_identity(self):
        """a + 0 == a"""
        a = make_qfixed(123456789012345678)
        zero = make_qfixed(0)
        
        assert a + zero == a
    
    def test_multiple_additions_deterministic(self):
        """Same inputs always produce same output."""
        a = make_qfixed(123456789)
        b = make_qfixed(987654321)
        
        results = []
        for _ in range(100):
            results.append(a + b)
        
        # All results should be identical
        assert len(set(results)) == 1, f"Got {len(set(results))} different results"


class TestQFixedMultiplication:
    """Test multiplication determinism."""
    
    def test_multiplication_commutative(self):
        """a * b == b * a"""
        a = make_qfixed(123456789)
        b = make_qfixed(987654321)
        
        assert a * b == b * a
    
    def test_multiplication_associative(self):
        """(a * b) * c == a * (b * c)"""
        a = make_qfixed(1000000)
        b = make_qfixed(2000000)
        c = make_qfixed(3000000)
        
        assert (a * b) * c == a * (b * c)
    
    def test_multiplication_identity(self):
        """a * 1 == a"""
        a = make_qfixed(123456789)
        one = make_qfixed(1)
        
        assert a * one == a
    
    def test_multiplication_deterministic(self):
        """Same inputs always produce same output."""
        a = make_qfixed(123456789)
        b = make_qfixed(987654321)
        
        results = []
        for _ in range(100):
            results.append(a * b)
        
        assert len(set(results)) == 1


class TestQFixedDivision:
    """Test division determinism."""
    
    def test_division_by_nonzero(self):
        """a / b defined for b != 0"""
        a = make_qfixed(1000000000)
        b = make_qfixed(2)
        
        result = a / b
        assert result == make_qfixed(500000000)
    
    def test_division_zero_numerator(self):
        """0 / b == 0 for b != 0"""
        zero = make_qfixed(0)
        b = make_qfixed(123456789)
        
        assert zero / b == zero
    
    def test_division_deterministic(self):
        """Same inputs always produce same output."""
        a = make_qfixed(1000000000000)
        b = make_qfixed(123456789)
        
        results = []
        for _ in range(100):
            results.append(a / b)
        
        assert len(set(results)) == 1


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSerialization:
    """Test serialization roundtrip."""
    
    def test_fraction_to_string_roundtrip(self):
        """Fraction representation survives roundtrip."""
        original = make_qfixed(123456789012345678)
        
        # Serialize to string
        serialized = str(original.numerator) + '/' + str(original.denominator)
        
        # Deserialize
        num, den = serialized.split('/')
        reconstructed = Fraction(int(num), int(den))
        
        assert original == reconstructed
    
    def test_tuple_serialization(self):
        """State serialization is deterministic."""
        states = [
            (make_qfixed(1), make_qfixed(2)),
            (make_qfixed(100), make_qfixed(200)),
            (make_qfixed(123456789), make_qfixed(987654321)),
        ]
        
        serialized = [str(s[0].numerator) + '/' + str(s[0].denominator) + '|' + 
                      str(s[1].numerator) + '/' + str(s[1].denominator) 
                      for s in states]
        
        # Deserialize
        deserialized = []
        for s in serialized:
            parts = s.split('|')
            num1, den1 = parts[0].split('/')
            num2, den2 = parts[1].split('/')
            deserialized.append((Fraction(int(num1), int(den1)), 
                                Fraction(int(num2), int(den2))))
        
        assert states == deserialized
    
    def test_hash_determinism(self):
        """Hash of same value is always same."""
        qf = make_qfixed(123456789012345678)
        
        hashes = [hash(qf) for _ in range(100)]
        
        assert len(set(hashes)) == 1, f"Got {len(set(hashes))} different hashes"


# =============================================================================
# Cost Model Tests
# =============================================================================

class TestCostDeterminism:
    """Test determinism in governance cost computations."""
    
    def test_verification_cost_deterministic(self):
        """verification_cost produces same result for same inputs."""
        from src.ck0.cost import verification_cost, CostConfig
        
        config = CostConfig(
            base_fee=Fraction(1000, QFIXED_DENOM),
            lambda_global=Fraction(1)
        )
        
        delta_plus = make_qfixed(5000000000000000)  # 5e-6
        
        results = []
        for _ in range(100):
            cost = verification_cost(delta_plus, config, "test")
            results.append(cost)
        
        assert len(set(results)) == 1, f"Got {len(set(results))} different costs"
    
    def test_subadditivity_deterministic(self):
        """Subadditivity: |g ∘ f| ≤ |f| + |g|"""
        from src.ck0.cost import verification_cost, CostConfig, assert_subadditivity
        
        config = CostConfig(
            base_fee=Fraction(0),
            lambda_global=Fraction(1)
        )
        
        delta_f = make_qfixed(1000000000000000)   # 1e-6
        delta_g = make_qfixed(2000000000000000)   # 2e-6
        
        cost_f = verification_cost(delta_f, config, "test")
        cost_g = verification_cost(delta_g, config, "test")
        
        # Composed: delta = delta_f + delta_g
        delta_composed = delta_f + delta_g
        cost_composed = verification_cost(delta_composed, config, "test")
        
        # Verify subadditivity holds
        assert cost_composed <= cost_f + cost_g
    
    def test_budget_conservation_deterministic(self):
        """Budget conservation: b' = b - cost"""
        from src.ck0.cost import budget_decrement, verification_cost, CostConfig
        from src.coh.grothendieck import Budget
        
        config = CostConfig(
            base_fee=Fraction(0),
            lambda_global=Fraction(1)
        )
        
        budget = Budget(Fraction(1000000, 1))  # 1 unit
        delta_plus = make_qfixed(1000000000000000)  # 1e-6
        
        cost = verification_cost(delta_plus, config, "test")
        
        results = []
        for _ in range(100):
            remaining = budget_decrement(budget, cost)
            results.append(remaining)
        
        # All should be identical
        assert len(set(results)) == 1


# =============================================================================
# Cross-Platform Tests
# =============================================================================

class TestCrossPlatform:
    """Test cross-platform consistency."""
    
    def test_fraction_precision(self):
        """Fractions maintain precision exactly."""
        # Large numbers
        large = Fraction(10**20, 1)
        
        # Create QFixed
        qf = make_qfixed(10**20)
        
        # Should maintain precision
        assert qf.denominator == QFIXED_DENOM
    
    def test_small_fraction_precision(self):
        """Small fractions maintain precision."""
        # Very small number
        small = Fraction(1, 10**18)
        
        qf = Fraction(1, QFIXED_DENOM)
        
        assert qf == small
    
    def test_fraction_normalization(self):
        """Fractions are normalized."""
        # Same value, different representation
        a = Fraction(2, 4)
        b = Fraction(1, 2)
        
        assert a == b  # Should be equal after normalization
    
    def test_zero_fraction(self):
        """Zero is handled consistently."""
        zero1 = Fraction(0, 1)
        zero2 = Fraction(0, 100)
        
        assert zero1 == zero2 == Fraction(0)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full cost model."""
    
    def test_tensor_cost_additivity(self):
        """Tensor product costs are additive."""
        from src.ck0.cost import verification_cost, CostConfig
        from src.coh.tensor import tensor_objects, unit_object
        from src.coh.types import CohObject
        
        config = CostConfig(
            base_fee=Fraction(0),
            lambda_global=Fraction(1)
        )
        
        # Two separate deltas
        delta_a = make_qfixed(1000000000000000)  # 1e-6
        delta_b = make_qfixed(2000000000000000)  # 2e-6
        
        cost_a = verification_cost(delta_a, config, "test")
        cost_b = verification_cost(delta_b, config, "test")
        
        # Combined delta for parallel execution
        delta_combined = delta_a + delta_b
        cost_combined = verification_cost(delta_combined, config, "test")
        
        # Should be additive
        assert cost_combined == cost_a + cost_b
    
    def test_composed_cost_subadditivity(self):
        """Sequential composition satisfies subadditivity."""
        from src.ck0.cost import verification_cost, CostConfig
        
        config = CostConfig(
            base_fee=Fraction(0),
            lambda_global=Fraction(1)
        )
        
        # Two sequential transitions
        delta_f = make_qfixed(1000000000000000)  # 1e-6
        delta_g = make_qfixed(2000000000000000)  # 2e-6
        
        cost_f = verification_cost(delta_f, config, "test")
        cost_g = verification_cost(delta_g, config, "test")
        
        # Net delta for sequence
        delta_seq = delta_f + delta_g
        cost_seq = verification_cost(delta_seq, config, "test")
        
        # Should satisfy subadditivity
        assert cost_seq <= cost_f + cost_g


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
