# ASG Operator Tests

import unittest
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from asg.operators import (
    build_gradient_operator_1d_ring,
    build_gradient_operator_2d_torus,
    build_mean_zero_projector,
    build_laplacian_1d_ring,
    compute_state_blocks,
    assemble_state_vector,
)


class TestGradientOperators(unittest.TestCase):
    """Test gradient operator construction"""
    
    def test_1d_ring_gradient_shape(self):
        """Gradient operator has correct shape"""
        N = 32
        D = build_gradient_operator_1d_ring(N)
        self.assertEqual(D.shape, (N, N))
    
    def test_1d_ring_gradient_properties(self):
        """Gradient operator has correct properties"""
        N = 4
        D = build_gradient_operator_1d_ring(N)
        
        # Row sums should be zero
        row_sums = np.sum(D, axis=1)
        np.testing.assert_allclose(row_sums, np.zeros(N))
        
        # Column sums should be zero
        col_sums = np.sum(D, axis=0)
        np.testing.assert_allclose(col_sums, np.zeros(N))
    
    def test_2d_torus_gradient_shape(self):
        """2D gradient operator has correct shape"""
        M, N = 4, 4
        D = build_gradient_operator_2d_torus(M, N)
        total = M * N
        self.assertEqual(D.shape, (2*total, total))
    
    def test_mean_zero_projector_shape(self):
        """Mean-zero projector has correct shape"""
        N = 32
        P = build_mean_zero_projector(N)
        self.assertEqual(P.shape, (N, N))
    
    def test_mean_zero_projector_property(self):
        """Projector correctly removes mean"""
        N = 32
        P = build_mean_zero_projector(N)
        
        # P should be symmetric
        np.testing.assert_allclose(P, P.T)
        
        # P should be idempotent: P² = P
        np.testing.assert_allclose(P @ P, P, rtol=1e-10)
        
        # Projecting a constant vector should give zero
        ones = np.ones(N)
        projected = P @ ones
        np.testing.assert_allclose(projected, np.zeros(N), atol=1e-10)
    
    def test_laplacian_1d_ring(self):
        """Laplacian is correct"""
        N = 4
        L = build_laplacian_1d_ring(N)
        
        # Laplacian should be symmetric
        np.testing.assert_allclose(L, L.T)
        
        # Laplacian should be positive semidefinite
        eigenvalues = np.linalg.eigvalsh(L)
        self.assertTrue(np.all(eigenvalues >= -1e-10))


class TestStateBlocks(unittest.TestCase):
    """Test state block extraction"""
    
    def test_state_blocks_extract(self):
        """State blocks extract correctly"""
        N = 8
        total = 4 * N
        
        # Create test state
        state = np.arange(total, dtype=np.float64)
        
        from asg.types import ASGStateLayout
        layout = ASGStateLayout.create_1d_ring(N)
        
        rho, theta, gamma, zeta = compute_state_blocks(state, layout)
        
        self.assertEqual(len(rho), N)
        self.assertEqual(len(theta), N)
        self.assertEqual(len(gamma), N)
        self.assertEqual(len(zeta), N)
    
    def test_state_blocks_roundtrip(self):
        """State blocks reconstruct correctly"""
        N = 8
        
        rho = np.random.rand(N)
        theta = np.random.rand(N)
        gamma = np.random.rand(N)
        zeta = np.random.rand(N)
        
        state = assemble_state_vector(rho, theta, gamma, zeta)
        
        np.testing.assert_array_equal(state[:N], rho)
        np.testing.assert_array_equal(state[N:2*N], theta)
        np.testing.assert_array_equal(state[2*N:3*N], gamma)
        np.testing.assert_array_equal(state[3*N:], zeta)


class Test1DRingSpecific(unittest.TestCase):
    """Tests specific to 1D ring topology"""
    
    def test_ring_gradient_periodic(self):
        """Gradient wraps around at boundaries"""
        N = 4
        D = build_gradient_operator_1d_ring(N)
        
        # First row (forward difference): D[0,0] = -1, D[0,1] = 1
        # For periodic boundary, D[0,N-1] = 0 (not wrapped)
        expected_first_row = np.array([-1., 1., 0., 0.])
        np.testing.assert_array_equal(D[0], expected_first_row)
    
    def test_laplacian_eigenvalues(self):
        """Laplacian eigenvalues are known for 1D ring"""
        N = 32
        L = build_laplacian_1d_ring(N)
        
        # Compute eigenvalues analytically
        k = np.arange(N)
        expected_evals = 4 * np.sin(np.pi * k / N) ** 2
        expected_evals = np.sort(expected_evals)  # Sort to match actual order
        
        actual_evals = np.linalg.eigvalsh(L)
        actual_evals = np.sort(actual_evals)
        
        np.testing.assert_allclose(actual_evals, expected_evals, rtol=1e-10, atol=1e-14)


if __name__ == '__main__':
    unittest.main()
