# ASG Spectral Tests

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from asg.types import ASGStateLayout, ASGParams
from asg.operators import build_mean_zero_projector
from asg.assembly import assemble_full_jacobian, assemble_hessian_model, project_hessian
from asg.spectral import (
    estimate_kappa_0,
    compute_semantic_direction,
    compute_semantic_rayleigh,
    compute_margin,
    verify_stability_conditions,
)


class TestKappaEstimation(unittest.TestCase):
    """Test κ₀ estimation"""
    
    def test_kappa_nonzero_for_pd_hessian(self):
        """κ₀ > 0 for positive definite Hessian"""
        # Create a simple PD matrix
        H = np.eye(10) * 2.0
        
        P = build_mean_zero_projector(10)
        H_perp = project_hessian(H, P)
        
        kappa = estimate_kappa_0(H_perp)
        self.assertGreater(kappa, 0)
    
    def test_kappa_zero_for_zero_hessian(self):
        """κ₀ = 0 for zero Hessian"""
        H = np.zeros((10, 10))
        
        P = build_mean_zero_projector(10)
        H_perp = project_hessian(H, P)
        
        kappa = estimate_kappa_0(H_perp)
        self.assertEqual(kappa, 0.0)
    
    def test_kappa_clamp_negative(self):
        """κ₀ = 0 when eigenvalues slightly negative (numerical)"""
        # Create a matrix with tiny negative eigenvalues
        H = np.eye(5) * 0.1
        H[0, 0] = -1e-12  # Tiny negative due to numerical error
        
        P = build_mean_zero_projector(5)
        H_perp = project_hessian(H, P)
        
        kappa = estimate_kappa_0(H_perp)
        # Should clamp to 0
        self.assertGreaterEqual(kappa, 0)


class TestSemanticDirection(unittest.TestCase):
    """Test semantic direction computation"""
    
    def test_semantic_direction_shape(self):
        """Semantic direction has correct shape"""
        N = 32
        layout = ASGStateLayout.create_1d_ring(N)
        state = np.random.rand(4 * N)
        
        v_sem = compute_semantic_direction(state, layout)
        
        self.assertEqual(v_sem.shape[0], 4 * N)
    
    def test_semantic_direction_form(self):
        """Semantic direction = (0, G, -θ, 0)"""
        N = 8
        layout = ASGStateLayout.create_1d_ring(N)
        
        # Create state with known values
        rho = np.ones(N) * 1.0
        theta = np.arange(N, dtype=np.float64)
        gamma = np.arange(N, dtype=np.float64) * 2.0
        zeta = np.zeros(N)
        
        state = np.concatenate([rho, theta, gamma, zeta])
        
        v_sem = compute_semantic_direction(state, layout)
        
        # Check structure
        np.testing.assert_array_almost_equal(v_sem[:N], np.zeros(N))  # rho block = 0
        np.testing.assert_array_almost_equal(v_sem[N:2*N], -theta)  # theta block = -θ
        np.testing.assert_array_almost_equal(v_sem[2*N:3*N], gamma)  # gamma block = G
        np.testing.assert_array_almost_equal(v_sem[3*N:], np.zeros(N))  # zeta block = 0


class TestSemanticRayleigh(unittest.TestCase):
    """Test semantic Rayleigh quotient"""
    
    def test_rayleigh_equals_hessian_eval_for_eigenvector(self):
        """Γ_sem = λ when v is eigenvector"""
        N = 5
        # Create diagonal Hessian
        eigenvalues = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        H = np.diag(eigenvalues)
        
        P = build_mean_zero_projector(N)
        H_perp = project_hessian(H, P)
        
        # Use first eigenvector (should have smallest eigenvalue)
        v = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
        
        gamma = compute_semantic_rayleigh(H_perp, v)
        
        # Should equal the eigenvalue
        self.assertAlmostEqual(gamma, eigenvalues[0], places=5)
    
    def test_rayleigh_positive_for_psd(self):
        """Γ_sem ≥ 0 for PSD Hessian"""
        # Create random PSD matrix
        A = np.random.rand(10, 10)
        H = A.T @ A  # Always PSD
        
        P = build_mean_zero_projector(10)
        H_perp = project_hessian(H, P)
        
        v = np.random.rand(10)
        gamma = compute_semantic_rayleigh(H_perp, v)
        
        self.assertGreaterEqual(gamma, 0)


class TestMargin(unittest.TestCase):
    """Test semantic margin computation"""
    
    def test_margin_infinity_when_kappa_zero(self):
        """M = ∞ when κ₀ = 0 and Γ_sem > 0"""
        gamma = 1.0
        kappa = 0.0
        
        margin = compute_margin(gamma, kappa)
        
        self.assertEqual(margin, float('inf'))
    
    def test_margin_zero_when_gamma_zero(self):
        """M = 0 when Γ_sem = 0"""
        gamma = 0.0
        kappa = 1.0
        
        margin = compute_margin(gamma, kappa)
        
        self.assertEqual(margin, 0.0)
    
    def test_margin_ratio(self):
        """M = Γ/κ"""
        gamma = 10.0
        kappa = 2.0
        
        margin = compute_margin(gamma, kappa)
        
        self.assertEqual(margin, 5.0)


class TestStabilityConditions(unittest.TestCase):
    """Test stability condition verification"""
    
    def test_all_pass_conditions(self):
        """All conditions pass"""
        result = verify_stability_conditions(
            kappa_0=1e-4,
            gamma_sem=1.0,
            margin=10.0,
            kappa_min=1e-6,
            margin_min=1.0
        )
        
        self.assertTrue(result["all_passed"])
    
    def test_kappa_fail(self):
        """κ₀ below threshold fails"""
        result = verify_stability_conditions(
            kappa_0=1e-8,
            gamma_sem=1.0,
            margin=10.0,
            kappa_min=1e-6,
            margin_min=1.0
        )
        
        self.assertFalse(result["all_passed"])
        self.assertFalse(result["kappa_adequate"])
    
    def test_margin_fail(self):
        """Margin below threshold fails"""
        result = verify_stability_conditions(
            kappa_0=1e-4,
            gamma_sem=0.1,
            margin=0.5,
            kappa_min=1e-6,
            margin_min=1.0
        )
        
        self.assertFalse(result["all_passed"])
        self.assertFalse(result["margin_adequate"])


class TestFullSpectralCertificate(unittest.TestCase):
    """Test full spectral certificate computation"""
    
    def test_asg_pipeline(self):
        """Full ASG pipeline runs"""
        N = 16
        layout = ASGStateLayout.create_1d_ring(N)
        
        weights = [1.0] * N
        params = ASGParams(
            state_layout=layout,
            weights=weights,
            alpha_l=1.0,
            alpha_g=1.0,
            w_theta=1.0,
        )
        
        # Build Jacobian and Hessian
        jacobian = assemble_full_jacobian(params, "1d_ring")
        H = assemble_hessian_model(jacobian)
        
        # Build projector
        P = build_mean_zero_projector(N)
        
        # Create state
        state = np.random.rand(4 * N)
        
        # Project Hessian
        H_perp = project_hessian(H, P)
        
        # Compute κ₀
        kappa = estimate_kappa_0(H_perp)
        
        # Compute semantic direction
        v_sem = compute_semantic_direction(state, layout)
        v_sem_perp = P @ v_sem
        
        # Compute Γ_sem
        gamma = compute_semantic_rayleigh(H_perp, v_sem_perp)
        
        # Compute margin
        margin = compute_margin(gamma, kappa)
        
        # All should be non-negative
        self.assertGreaterEqual(kappa, 0)
        self.assertGreaterEqual(gamma, 0)
        self.assertGreaterEqual(margin, 0)


if __name__ == '__main__':
    unittest.main()
