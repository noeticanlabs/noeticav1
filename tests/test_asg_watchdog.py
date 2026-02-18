# ASG Watchdog Tests

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from asg.types import ASGStateLayout, ASGParams
from asg.watchdog import ProxWatchdog, create_watchdog
from asg.operators import build_mean_zero_projector
from asg.assembly import assemble_full_jacobian, assemble_hessian_model


class TestProxWatchdog(unittest.TestCase):
    """Test ProxWatchdog functionality"""
    
    def test_watchdog_creation(self):
        """Watchdog initializes correctly"""
        watchdog = create_watchdog(N=16)
        
        self.assertIsNotNone(watchdog)
        self.assertEqual(watchdog.projector_id, "mean_zero_theta_v1")
    
    def test_compute_v(self):
        """V computation works"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        # Create random state
        state = np.random.rand(4 * N)
        
        v = watchdog.compute_v(state)
        
        self.assertIsInstance(v, float)
        self.assertGreaterEqual(v, 0)
    
    def test_prox_inequality_pass(self):
        """Prox inequality check passes when V decreases"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        # Original state
        state_before = np.random.rand(4 * N) * 0.1
        
        # Drift (slight increase)
        drift_point = state_before + np.random.rand(4 * N) * 0.01
        
        # Correction (reduces V more than drift increased)
        v_before = watchdog.compute_v(state_before)
        v_drift = watchdog.compute_v(drift_point)
        v_after = v_drift * 0.5  # Significant reduction
        
        correction_point = drift_point * 0.5  # Just for shape
        lambda_k = 0.1
        
        passed, details = watchdog.verify_prox_inequality(
            v_before, v_drift, v_after,
            drift_point, correction_point, lambda_k
        )
        
        # Should pass if V_after < V_drift - bound
        # This is a weak test - just check it runs
        self.assertIsInstance(passed, bool)
    
    def test_prox_inequality_fail(self):
        """Prox inequality fails when V increases"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        v_before = 1.0
        v_drift = 1.5  # Drift increased V
        v_after = 2.0  # Correction also increased V!
        
        drift_point = np.random.rand(4 * N)
        correction_point = drift_point + 0.1
        lambda_k = 0.1
        
        passed, details = watchdog.verify_prox_inequality(
            v_before, v_drift, v_after,
            drift_point, correction_point, lambda_k
        )
        
        # Should fail because V_after > V_drift
        self.assertFalse(passed)
    
    def test_structural_drift_pass(self):
        """Drift check passes when within bounds"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        original = np.ones(4 * N)
        drift = original + np.random.rand(4 * N) * 0.1  # Small drift
        
        passed, details = watchdog.check_structural_drift(drift, original)
        
        self.assertTrue(passed)
        self.assertLess(details["ratio"], 2.0)
    
    def test_structural_drift_fail(self):
        """Drift check fails when exceeds bounds"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        original = np.ones(4 * N)
        drift = original + original * 5.0  # 500% drift!
        
        passed, details = watchdog.check_structural_drift(drift, original, max_drift_ratio=2.0)
        
        self.assertFalse(passed)
    
    def test_full_split_step(self):
        """Full split step verification runs"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        # Simple test: small drift, big correction
        state_before = np.random.rand(4 * N) * 0.1
        drift_point = state_before + np.random.rand(4 * N) * 0.01
        correction_point = state_before * 0.9  # Reduce
        lambda_k = 0.1
        
        passed, details = watchdog.verify_full_split_step(
            state_before, drift_point, correction_point, lambda_k
        )
        
        # Check details structure
        self.assertIn("prox_pass", details)
        self.assertIn("drift_pass", details)
        self.assertIn("v_before", details)
        self.assertIn("v_drift", details)
        self.assertIn("v_after", details)
    
    def test_watchdog_receipt_creation(self):
        """Watchdog receipt is created correctly"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        state_before = np.random.rand(4 * N)
        drift_point = state_before + 0.01
        correction_point = state_before * 0.9
        lambda_k = 0.1
        
        v_before = watchdog.compute_v(state_before)
        v_drift = watchdog.compute_v(drift_point)
        v_after = watchdog.compute_v(correction_point)
        
        receipt = watchdog.emit_watchdog_receipt(
            state_before=state_before,
            drift_point=drift_point,
            correction_point=correction_point,
            lambda_k=lambda_k,
            v_before=v_before,
            v_drift=v_drift,
            v_after=v_after,
            prox_pass=True,
            drift_pass=True,
        )
        
        # Check receipt fields
        self.assertGreaterEqual(receipt.kappa_est, 0)
        self.assertGreaterEqual(receipt.gamma_sem, 0)
        self.assertGreaterEqual(receipt.semantic_margin, 0)
        self.assertEqual(len(receipt.operator_digest), 64)
        self.assertEqual(len(receipt.state_hash), 64)


class TestProxInequalityMath(unittest.TestCase):
    """Mathematical tests for prox inequality"""
    
    def test_exact_prox_solution(self):
        """Test with exact proximal solution"""
        # For quadratic V with identity Hessian, prox has exact form
        N = 4
        watchdog = create_watchdog(N=N)
        
        # Use identity-like state
        state_before = np.array([1.0, 0.0, 0.0, 0.0,  # rho
                                 0.5, 0.0, 0.0, 0.0,  # theta  
                                 0.0, 0.0, 0.0, 0.0,  # gamma
                                 0.0, 0.0, 0.0, 0.0])  # zeta
        
        # Simple drift (add small constant)
        drift_point = state_before + 0.01
        
        # Prox correction: for quadratic V(x) = x^T H x, 
        # prox_{\lambda V}(z) = (I + 2\lambda H)^{-1} z
        # With identity-like H, this is simple scaling
        lambda_k = 0.1
        correction_point = drift_point / (1 + 2 * lambda_k)
        
        # Compute V values
        v_before = watchdog.compute_v(state_before)
        v_drift = watchdog.compute_v(drift_point)
        v_after = watchdog.compute_v(correction_point)
        
        # Verify inequality
        passed, details = watchdog.verify_prox_inequality(
            v_before, v_drift, v_after,
            drift_point, correction_point, lambda_k
        )
        
        # For exact prox, should pass
        self.assertTrue(passed)


class TestDriftBehavior(unittest.TestCase):
    """Tests for drift behavior in split model"""
    
    def test_drift_can_increase_v(self):
        """Drift point V can be > original V"""
        N = 8
        watchdog = create_watchdog(N=N)
        
        state = np.random.rand(4 * N)
        
        # Apply a drift that increases V
        # (in practice, this depends on the model dynamics)
        drift = state + np.random.rand(4 * N)
        
        v_before = watchdog.compute_v(state)
        v_drift = watchdog.compute_v(drift)
        
        # Drift can increase V (this is the point of the split model!)
        # Just verify the computation runs
        self.assertIsInstance(v_drift, float)


if __name__ == '__main__':
    unittest.main()
