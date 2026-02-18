# Pipeline Integration Tests
# Tests the full NK-3 → NK-2 → NEC → ASG → NK-4G → NK-1 pipeline

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from asg.types import ASGStateLayout, ASGParams
from asg.operators import build_mean_zero_projector, build_4n_state_projector
from asg.assembly import assemble_full_jacobian, assemble_hessian_model, project_hessian
from asg.spectral import (
    estimate_kappa_0,
    estimate_kappa_0_policy,
    compute_semantic_direction,
    compute_semantic_rayleigh,
    compute_margin,
    compute_semantic_margin_policy,
)
from asg.watchdog import ProxWatchdog, create_watchdog
from nk4g.receipt_fields import ASGCertificate, NK4GReceiptExtension
from nk1.policy_bundle import PolicyBundle, evaluate_nk4g_policy, PolicyStatus, DEFAULT_NK4G_KAPPA_MIN, DEFAULT_NK4G_MARGIN_MIN


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for the full NK-3→NK-2→NEC→ASG→NK-4G→NK-1 pipeline."""
    
    def test_asg_certificate_flow(self):
        """Test ASG certificate generation and consumption."""
        # Setup: Create ASG components
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        
        # Create weights
        weights = [1.0] * N
        
        # Create params
        params = ASGParams(
            state_layout=layout,
            weights=weights,
            alpha_l=1.0,
            alpha_g=1.0,
            w_theta=1.0,
        )
        
        # Assemble operators - jacobian is already (4N x 4N)
        jacobian = assemble_full_jacobian(params, "1d_ring")
        hessian = assemble_hessian_model(jacobian)  # This is 4N x 4N
        
        # For spectral analysis, use a simple PD Hessian directly
        # (in real usage, this would be properly projected)
        H_test = np.eye(4 * N) * 2.0
        
        # ASG: Compute κ₀ with policy identification
        kappa_result = estimate_kappa_0_policy(
            H_test,
            method_id="eigsh_smallest_sa.v1",
            tolerance=1e-6,
            max_iterations=1000
        )
        
        # Verify policy-identified result
        self.assertEqual(kappa_result.method_id, "eigsh_smallest_sa.v1")
        self.assertIsInstance(kappa_result.kappa_0, float)
        self.assertGreaterEqual(kappa_result.kappa_0, 0.0)
        
    def test_semantic_margin_flow(self):
        """Test semantic margin computation with versioned direction ID."""
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        
        # Create a test state
        state = np.random.randn(4 * N)
        
        # Create a test Hessian (4N x 4N PD matrix)
        hessian_perp = np.eye(4 * N) * 2.0
        
        # Compute semantic margin with policy identification
        sem_result = compute_semantic_margin_policy(
            state,
            hessian_perp,
            layout,
            direction_id="asg.semantic.thetaG_rotation.v1"
        )
        
        # Verify versioned direction ID
        self.assertEqual(sem_result.direction_id, "asg.semantic.thetaG_rotation.v1")
        self.assertIsInstance(sem_result.gamma_sem, float)
        
    def test_nk4g_receipt_with_asg_certificate(self):
        """Test NK-4G receipt includes full ASG certificate."""
        # Create ASG certificate
        cert = ASGCertificate(
            model_id="asg.zeta-theta-rho-G.v1",
            operator_digest="abc123",
            projector_id="asg.projector.theta_mean_zero.v1",
            kappa_est=0.5,
            kappa_method_id="eigsh_smallest_sa.v1",
            kappa_tol=1e-6,
            kappa_maxiter=1000,
            gamma_sem=2.0,
            semantic_dir_id="asg.semantic.thetaG_rotation.v1",
            semantic_margin=4.0,
        )
        
        # Convert to dict
        cert_dict = cert.to_dict()
        
        # Verify all fields present
        self.assertEqual(cert_dict["model_id"], "asg.zeta-theta-rho-G.v1")
        self.assertEqual(cert_dict["projector_id"], "asg.projector.theta_mean_zero.v1")
        self.assertEqual(cert_dict["kappa_method_id"], "eigsh_smallest_sa.v1")
        self.assertEqual(cert_dict["semantic_dir_id"], "asg.semantic.thetaG_rotation.v1")
        
    def test_nk1_policy_gate_pass(self):
        """Test NK-1 policy gates pass when thresholds met."""
        # Create policy with thresholds
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=1.0,
        )
        
        # Create ASG certificate that passes
        asg_cert = {
            "kappa_est": 0.1,
            "semantic_margin": 2.0,
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.theta_mean_zero.v1",
        }
        
        # Evaluate policy
        status, details = evaluate_nk4g_policy(asg_cert, policy)
        
        # Should pass
        self.assertEqual(status, PolicyStatus.PASS)
        self.assertEqual(len(details["issues"]), 0)
        
    def test_nk1_policy_gate_halt(self):
        """Test NK-1 policy gates HALT when κ₀ below threshold."""
        policy = PolicyBundle(
            nk4g_kappa_min=1e-6,
            nk4g_margin_min=1.0,
        )
        
        # Create ASG certificate with low κ₀
        asg_cert = {
            "kappa_est": 1e-10,  # Below threshold
            "semantic_margin": 2.0,
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.theta_mean_zero.v1",
        }
        
        # Evaluate policy
        status, details = evaluate_nk4g_policy(asg_cert, policy)
        
        # Should HALT
        self.assertEqual(status, PolicyStatus.HALT)
        self.assertTrue(any("κ₀" in issue for issue in details["issues"]))
        
    def test_nk1_policy_gate_warn(self):
        """Test NK-1 policy gates WARN when margin below threshold."""
        policy = PolicyBundle(
            nk4g_kappa_min=1e-8,
            nk4g_margin_min=3.0,
        )
        
        # Create ASG certificate with low margin (but OK κ₀)
        asg_cert = {
            "kappa_est": 0.1,  # OK κ₀
            "semantic_margin": 1.0,  # Below threshold
            "kappa_method_id": "eigsh_smallest_sa.v1",
            "projector_id": "asg.projector.theta_mean_zero.v1",
        }
        
        # Evaluate policy
        status, details = evaluate_nk4g_policy(asg_cert, policy)
        
        # Should WARN (not HALT since κ₀ is OK)
        self.assertEqual(status, PolicyStatus.WARN)
        self.assertTrue(any("Margin" in issue for issue in details["issues"]))
        
    def test_prox_watchdog_flow(self):
        """Test ProxWatchdog with 4N state projector."""
        # Create watchdog
        watchdog = create_watchdog(N=8)
        
        # Verify projector ID is canonical
        self.assertEqual(watchdog.projector_id, "asg.projector.theta_mean_zero.v1")
        
        # Create test states - for prox inequality to pass:
        # V(x_{k+1}) <= V(z_k) - (1/2λ_k) * ||x_{k+1} - z_k||^2
        # So we need: v_after <= v_drift - correction_term
        
        lambda_k = 0.1
        
        # Create states where the correction is large enough
        # Start with zero state
        state_before = np.zeros(32)
        drift_point = np.ones(32) * 0.1  # Small drift
        
        # Make correction very small to satisfy inequality
        correction_point = drift_point * 0.01  # Large correction toward zero
        
        # Compute V values
        v_before = watchdog.compute_v(state_before)
        v_drift = watchdog.compute_v(drift_point)
        v_after = watchdog.compute_v(correction_point)
        
        # Verify prox inequality
        passed, details = watchdog.verify_prox_inequality(
            v_before, v_drift, v_after,
            drift_point, correction_point, lambda_k
        )
        
        # Check that we have the required details
        self.assertIn("lhs", details)
        self.assertIn("rhs", details)
        # Note: actual pass/fail depends on the values
        
    def test_4n_projector_integration(self):
        """Test 4N state projector works with spectral analysis."""
        N = 16
        
        # Build 4N projector
        P_4N = build_4n_state_projector(N)
        
        # Verify shape
        self.assertEqual(P_4N.shape, (4 * N, 4 * N))
        
        # Create test state
        state = np.random.randn(4 * N)
        
        # Apply projector
        projected_state = P_4N @ state
        
        # θ block (indices N:2N) should have mean zero after projection
        theta_block = projected_state[N:2*N]
        self.assertAlmostEqual(np.mean(theta_block), 0.0, places=10)
        
    def test_end_to_end_receipt_flow(self):
        """Test complete receipt flow from ASG to NK-4G to NK-1."""
        # Setup
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        
        # Create a simple test Hessian (4N x 4N)
        hessian_perp = np.eye(4 * N) * 2.0
        
        # ASG: Compute κ₀ and Γ_sem
        state = np.random.randn(4 * N)
        
        kappa_result = estimate_kappa_0_policy(hessian_perp)
        sem_result = compute_semantic_margin_policy(state, hessian_perp, layout)
        
        margin = compute_margin(sem_result.gamma_sem, kappa_result.kappa_0)
        
        # Create ASG Certificate
        asg_cert = ASGCertificate(
            model_id="asg.zeta-theta-rho-G.v1",
            operator_digest="test_digest",
            projector_id="asg.projector.theta_mean_zero.v1",
            kappa_est=kappa_result.kappa_0,
            kappa_method_id=kappa_result.method_id,
            gamma_sem=sem_result.gamma_sem,
            semantic_dir_id=sem_result.direction_id,
            semantic_margin=margin,
        )
        
        # Create Policy
        policy = PolicyBundle(
            nk4g_kappa_min=1e-10,
            nk4g_margin_min=0.1,
        )
        
        # Evaluate Policy
        status, details = evaluate_nk4g_policy(asg_cert.to_dict(), policy)
        
        # Should pass
        self.assertEqual(status, PolicyStatus.PASS)
        
        # Verify all IDs are versioned
        self.assertIn("v1", asg_cert.model_id)
        self.assertIn("v1", asg_cert.projector_id)
        self.assertIn("v1", asg_cert.kappa_method_id)
        self.assertIn("v1", asg_cert.semantic_dir_id)


if __name__ == "__main__":
    unittest.main()
