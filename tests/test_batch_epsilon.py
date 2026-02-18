
# Tests for NK-1 Batch Epsilon Computation

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nk1.batch_epsilon import (
    BatchEpsilonConfig,
    VFunctional,
    Operation,
    compute_epsilon_B,
    compute_epsilon_hat,
    verify_gate,
    half_even_round
)


class TestHalfEvenRound(unittest.TestCase):
    """Tests for half_even_round."""
    
    def test_round_down(self):
        """Test rounding 0.4 -> 0."""
        self.assertEqual(half_even_round(0.4), 0)
    
    def test_round_up(self):
        """Test rounding 0.6 -> 1."""
        self.assertEqual(half_even_round(0.6), 1)
    
    def test_half_even_round_down(self):
        """Test 0.5 -> 0 (even)."""
        self.assertEqual(half_even_round(0.5), 0)
    
    def test_half_even_round_up(self):
        """Test 1.5 -> 2 (even)."""
        self.assertEqual(half_even_round(1.5), 2)
    
    def test_half_even_2_5(self):
        """Test 2.5 -> 2 (even)."""
        self.assertEqual(half_even_round(2.5), 2)
    
    def test_half_even_3_5(self):
        """Test 3.5 -> 4 (even)."""
        self.assertEqual(half_even_round(3.5), 4)


class TestVFunctional(unittest.TestCase):
    """Tests for VFunctional."""
    
    def test_v_evaluation(self):
        """Test V functional evaluation."""
        def simple_v(state):
            return state.get("debt", 0)
        
        v = VFunctional(simple_v)
        result = v.evaluate({"debt": 100})
        
        self.assertEqual(result, 100)
    
    def test_v_with_zero(self):
        """Test V with missing key."""
        v = VFunctional(lambda s: s.get("debt", 0))
        result = v.evaluate({})
        
        self.assertEqual(result, 0)


class TestOperation(unittest.TestCase):
    """Tests for Operation."""
    
    def test_apply(self):
        """Test operation apply."""
        def apply_op(state):
            return {"balance": state.get("balance", 0) + 50}
        
        op = Operation("op1", apply_op, ["balance"])
        result = op.apply({"balance": 100})
        
        self.assertEqual(result["balance"], 150)
    
    def test_patch(self):
        """Test operation patch with write set."""
        def apply_op(state):
            return {"balance": 200, "version": 99}
        
        op = Operation("op1", apply_op, ["balance"])
        
        original = {"balance": 100, "version": 1}
        delta = {"balance": 200, "version": 99}
        
        patched = op.patch(original, delta)
        
        # Only balance should be updated (in write set)
        self.assertEqual(patched["balance"], 200)
        self.assertEqual(patched["version"], 1)  # version unchanged
    
    def test_patch_empty_write_set(self):
        """Test patch with empty write set."""
        op = Operation("op1", lambda s: s, [])
        
        original = {"a": 1}
        delta = {"a": 2}
        
        patched = op.patch(original, delta)
        
        # Nothing should change
        self.assertEqual(patched["a"], 1)


class TestComputeEpsilonB(unittest.TestCase):
    """Tests for compute_epsilon_B."""
    
    def test_epsilon_b_simple(self):
        """Test epsilon B computation."""
        # Simple V: just return balance
        v_func = VFunctional(lambda s: s.get("balance", 0))
        
        # Operations
        op1 = Operation("op1", lambda s: {"balance": s.get("balance", 0) + 50}, ["balance"])
        
        state_before = {"balance": 100}
        
        def kernel_apply(state, op):
            return op.apply(state)
        
        eps, intermediates = compute_epsilon_B(state_before, [op1], v_func, kernel_apply)
        
        # Delta_B = V(150) - V(100) = 150 - 100 = 50
        # Delta_Sigma = same = 50
        # epsilon_B = 50 - 50 = 0
        self.assertEqual(eps, 0)
    
    def test_epsilon_b_interaction(self):
        """Test epsilon B computation - basic case."""
        # Simple V: just return balance
        v_func = VFunctional(lambda s: s.get("balance", 0))
        
        # Operation that increases balance
        op1 = Operation("op1", lambda s: {"balance": s.get("balance", 0) + 50}, ["balance"])
        
        state_before = {"balance": 100}
        
        def kernel_apply(state, op):
            return op.apply(state)
        
        eps, intermediates = compute_epsilon_B(state_before, [op1], v_func, kernel_apply)
        
        # For single op, epsilon_B should be 0 (patched = actual)
        self.assertEqual(eps, 0)


class TestComputeEpsilonHat(unittest.TestCase):
    """Tests for compute_epsilon_hat."""
    
    def test_identity_matrix(self):
        """Test with identity matrix."""
        # M = identity
        matrix = {(0, 0): 1.0}
        
        delta = [10]
        
        # delta^T * M * delta = 10 * 1 * 10 = 100
        result = compute_epsilon_hat(matrix, delta)
        
        self.assertEqual(result, 100)
    
    def test_with_scale(self):
        """Test with matrix scale."""
        matrix = {(0, 0): 1.0}
        delta = [10]
        
        # With scale 2: 10 * 1 * 10 * 2 = 200
        result = compute_epsilon_hat(matrix, delta, matrix_scale=2)
        
        self.assertEqual(result, 200)
    
    def test_symmetry(self):
        """Test matrix computation with single entry."""
        # Single matrix entry
        matrix = {(0, 1): 1.0}
        
        delta = [3, 4]
        
        result = compute_epsilon_hat(matrix, delta)
        
        # 2 * 1 * 3 * 4 = 24
        self.assertEqual(result, 24)


class TestVerifyGate(unittest.TestCase):
    """Tests for verify_gate."""
    
    def test_approved(self):
        """Test approved when epsilon <= hat."""
        approved, reason = verify_gate(50, 100)
        
        self.assertTrue(approved)
        self.assertIn("APPROVED", reason)
    
    def test_rejected(self):
        """Test rejected when epsilon > hat."""
        approved, reason = verify_gate(100, 50)
        
        self.assertFalse(approved)
        self.assertIn("REJECTED", reason)
    
    def test_equal(self):
        """Test approved when exactly equal."""
        approved, reason = verify_gate(50, 50)
        
        self.assertTrue(approved)


class TestBatchEpsilonConfig(unittest.TestCase):
    """Tests for BatchEpsilonConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = BatchEpsilonConfig()
        
        self.assertEqual(config.rounding_mode, "half_even")
        self.assertEqual(config.matrix_digest, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
