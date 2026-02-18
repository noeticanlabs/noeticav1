# ASG Watchdog - Prox Inequality Verification

import numpy as np
import hashlib
from dataclasses import dataclass
from typing import Optional, Tuple, List

from .types import ASGParams, ASGReceipt, ASGStateLayout
from .operators import build_mean_zero_projector, PROJECTOR_ID
from .assembly import assemble_full_jacobian, assemble_hessian_model, compute_operator_digest, compute_state_digest, compute_params_digest
from .spectral import estimate_kappa_0, compute_semantic_direction, compute_semantic_rayleigh, compute_margin


class ProxWatchdog:
    """Prox inequality verification for NEC split dynamics.
    
    The watchdog verifies the proximal correction inequality:
    
        V(x_{k+1}) ≤ V(z_k) - (1/2λ_k)||x_{k+1}-z_k||²
        
    Where:
        - z_k: Drift point (proposal from model)
        - x_{k+1}: Correction point (after prox)
        - λ_k: Prox parameter
    """
    
    def __init__(self, params: ASGParams, topology: str = "1d_ring"):
        """Initialize watchdog with ASG parameters.
        
        Args:
            params: ASG parameters
            topology: "1d_ring" or "2d_torus"
        """
        self.params = params
        self.topology = topology
        
        # Build projector for theta block
        self.projector = build_mean_zero_projector(params.state_layout.dimension)
        self.projector_id = PROJECTOR_ID  # "asg.projector.theta_mean_zero.v1"
        
        # Assemble Jacobian and Hessian
        self.jacobian = assemble_full_jacobian(params, topology)
        self.hessian = assemble_hessian_model(self.jacobian)
        
        # Compute operator digest
        self.operator_digest = compute_operator_digest(params, self.hessian)
    
    def compute_v(self, state: np.ndarray) -> float:
        """Compute V(state) = (1/2)||O·state||²
        
        Args:
            state: State vector
            
        Returns:
            V value (scalar)
        """
        residuals = self.jacobian @ state
        return 0.5 * np.dot(residuals, residuals)
    
    def compute_g_norm_squared(
        self,
        state1: np.ndarray,
        state2: np.ndarray
    ) -> float:
        """Compute G-norm squared: ||state1 - state2||_G²
        
        For simplicity, uses Euclidean norm. In full implementation,
        this would use the G-metric (diagonal weights).
        
        Args:
            state1: First state
            state2: Second state
            
        Returns:
            ||state1 - state2||²
        """
        diff = state1 - state2
        return np.dot(diff, diff)
    
    def verify_prox_inequality(
        self,
        v_before: float,
        v_drift: float,
        v_after: float,
        drift_point: np.ndarray,
        correction_point: np.ndarray,
        lambda_k: float
    ) -> Tuple[bool, dict]:
        """Verify: V(x_{k+1}) ≤ V(z_k) - (1/2λ_k)||x_{k+1}-z_k||²
        
        Args:
            v_before: V(x_k) - original state violation
            v_drift: V(z_k) - drift point violation  
            v_after: V(x_{k+1}) - corrected state violation
            drift_point: z_k
            correction_point: x_{k+1}
            lambda_k: Prox parameter λ_k
            
        Returns:
            Tuple of (pass: bool, details: dict)
        """
        # Compute the bound term
        norm_sq = self.compute_g_norm_squared(correction_point, drift_point)
        bound_term = norm_sq / (2 * lambda_k)
        
        # Check inequality
        rhs = v_drift - bound_term
        passed = v_after <= rhs
        
        details = {
            "v_before": v_before,
            "v_drift": v_drift,
            "v_after": v_after,
            "norm_squared": norm_sq,
            "lambda_k": lambda_k,
            "bound_term": bound_term,
            "rhs": rhs,
            "lhs": v_after,
            "margin": rhs - v_after if passed else v_after - rhs,
        }
        
        return passed, details
    
    def check_structural_drift(
        self,
        drift_point: np.ndarray,
        original_state: np.ndarray,
        max_drift_ratio: float = 2.0
    ) -> Tuple[bool, dict]:
        """Verify drift is within allowed bounds.
        
        Args:
            drift_point: z_k (after drift)
            original_state: x_k (before drift)
            max_drift_ratio: Maximum allowed ||z_k - x_k|| / ||x_k||
            
        Returns:
            Tuple of (pass: bool, details: dict)
        """
        drift_norm = np.linalg.norm(drift_point - original_state)
        original_norm = np.linalg.norm(original_state)
        
        if original_norm < 1e-10:
            # If original is near zero, just check drift is bounded
            passed = drift_norm < 1e-5
            ratio = 0.0
        else:
            ratio = drift_norm / original_norm
            passed = ratio <= max_drift_ratio
        
        details = {
            "drift_norm": drift_norm,
            "original_norm": original_norm,
            "ratio": ratio,
            "max_allowed": max_drift_ratio,
        }
        
        return passed, details
    
    def emit_watchdog_receipt(
        self,
        state_before: np.ndarray,
        drift_point: np.ndarray,
        correction_point: np.ndarray,
        lambda_k: float,
        v_before: float,
        v_drift: float,
        v_after: float,
        prox_pass: bool,
        drift_pass: bool,
        kappa_est: Optional[float] = None,
        gamma_sem: Optional[float] = None,
        margin: Optional[float] = None,
        estimation_method: str = "exact"
    ) -> ASGReceipt:
        """Emit deterministic watchdog receipt.
        
        Args:
            state_before: Original state x_k
            drift_point: Drift point z_k
            correction_point: Correction point x_{k+1}
            lambda_k: Prox parameter λ_k
            v_before: V(x_k)
            v_drift: V(z_k) 
            v_after: V(x_{k+1})
            prox_pass: Whether prox inequality passed
            drift_pass: Whether drift check passed
            kappa_est: κ₀ estimate (optional)
            gamma_sem: Γ_sem (optional)
            margin: Semantic margin (optional)
            estimation_method: Method used for κ₀
            
        Returns:
            ASGReceipt with all fields
        """
        # Compute hashes
        state_hash = compute_state_digest(state_before)
        params_hash = compute_params_digest(self.params)
        
        # Use defaults if not provided
        if kappa_est is None:
            # Project Hessian
            hessian_perp = self.projector @ self.hessian @ self.projector
            kappa_est = estimate_kappa_0(hessian_perp)
        
        if gamma_sem is None or margin is None:
            # Compute semantic direction and margin
            v_sem = compute_semantic_direction(correction_point, self.params.state_layout)
            v_sem_perp = self.projector @ v_sem
            
            hessian_perp = self.projector @ self.hessian @ self.projector
            
            if gamma_sem is None:
                gamma_sem = compute_semantic_rayleigh(hessian_perp, v_sem_perp)
            
            if margin is None:
                margin = compute_margin(gamma_sem, kappa_est)
        
        receipt = ASGReceipt(
            kappa_est=kappa_est,
            gamma_sem=gamma_sem,
            semantic_margin=margin,
            projector_id=self.projector_id,
            operator_digest=self.operator_digest,
            estimation_method=estimation_method,
            state_hash=state_hash,
            params_hash=params_hash,
        )
        
        return receipt
    
    def verify_full_split_step(
        self,
        state_before: np.ndarray,
        drift_point: np.ndarray,
        correction_point: np.ndarray,
        lambda_k: float,
        max_drift_ratio: float = 2.0
    ) -> Tuple[bool, dict]:
        """Verify complete split step (drift + correction).
        
        Args:
            state_before: x_k
            drift_point: z_k
            correction_point: x_{k+1}
            lambda_k: λ_k
            max_drift_ratio: Max allowed drift
            
        Returns:
            Tuple of (all_passed: bool, details: dict)
        """
        # Compute V values
        v_before = self.compute_v(state_before)
        v_drift = self.compute_v(drift_point)
        v_after = self.compute_v(correction_point)
        
        # Check prox inequality
        prox_pass, prox_details = self.verify_prox_inequality(
            v_before, v_drift, v_after,
            drift_point, correction_point, lambda_k
        )
        
        # Check drift bounds
        drift_pass, drift_details = self.check_structural_drift(
            drift_point, state_before, max_drift_ratio
        )
        
        all_passed = prox_pass and drift_pass
        
        details = {
            "prox_pass": prox_pass,
            "prox_details": prox_details,
            "drift_pass": drift_pass,
            "drift_details": drift_details,
            "v_before": v_before,
            "v_drift": v_drift,
            "v_after": v_after,
            "lambda_k": lambda_k,
        }
        
        return all_passed, details


def create_watchdog(
    N: int,
    alpha_l: float = 1.0,
    alpha_g: float = 1.0,
    w_theta: float = 1.0,
    topology: str = "1d_ring"
) -> ProxWatchdog:
    """Factory to create a ProxWatchdog with default parameters.
    
    Args:
        N: System size
        alpha_l: Linguistic coupling
        alpha_g: Gradient coupling
        w_theta: Theta penalty weight
        topology: "1d_ring" or "2d_torus"
        
    Returns:
        Configured ProxWatchdog
    """
    # Create state layout
    if topology == "1d_ring":
        layout = ASGStateLayout.create_1d_ring(N)
    else:
        M = int(np.sqrt(N))
        layout = ASGStateLayout.create_2d_torus(M, N // M)
    
    # Default weights (uniform)
    weights = [1.0] * layout.dimension
    
    # Create params
    params = ASGStateLayout(
        rho_start=0,
        theta_start=N,
        gamma_start=2*N,
        zeta_start=3*N,
        dimension=N,
    )
    
    # Need to create proper ASGParams
    from .types import ASGParams
    params = ASGParams(
        state_layout=layout,
        weights=weights,
        alpha_l=alpha_l,
        alpha_g=alpha_g,
        w_theta=w_theta,
    )
    
    return ProxWatchdog(params, topology)
