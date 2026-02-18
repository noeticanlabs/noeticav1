# ASG Spectral Analysis - κ₀, Γ_sem, and Margin Computation

import numpy as np
from typing import Optional, Tuple
from scipy import sparse
from scipy.sparse.linalg import eigsh, lobpcg


def estimate_kappa_0(
    hessian_perp: np.ndarray,
    method: str = "eigsh",
    k: int = 1
) -> float:
    """Estimate κ₀ = λ_min(H_⊥) - smallest eigenvalue of reduced Hessian.
    
    The smallest eigenvalue tells us the "stiffness floor" of the system.
    If κ₀ > 0, the reduced Hessian is positive definite.
    
    Args:
        hessian_perp: Projected Hessian (P_⊥ H P_⊥) of shape (n, n)
        method: Estimation method - "eigsh", "lobpcg", or "power"
        k: Number of eigenvalues to compute (for eigsh)
        
    Returns:
        κ₀ estimate (≥ 0 by construction since H = O^T O)
        
    Note:
        For H = O^T O, eigenvalues are guaranteed ≥ 0.
        Numerical errors may produce tiny negative values; we clamp to 0.
    """
    n = hessian_perp.shape[0]
    
    if n == 0:
        return 0.0
    
    if n == 1:
        return max(0.0, hessian_perp[0, 0])
    
    # Use sparse if matrix is large
    if n > 100:
        hessian_sparse = sparse.csr_matrix(hessian_perp)
    else:
        hessian_sparse = None
    
    if method == "eigsh":
        # Shifted power iteration to find smallest eigenvalue
        # Use k=1 to find the smallest
        try:
            if hessian_sparse is not None:
                eigenvalues, _ = eigsh(hessian_sparse, k=k, which='SA', maxiter=1000)
            else:
                eigenvalues, _ = np.linalg.eigvalsh(hessian_perp)
                eigenvalues = np.sort(eigenvalues)[:k]
        except Exception:
            # Fallback to dense computation
            eigenvalues = np.linalg.eigvalsh(hessian_perp)
            eigenvalues = np.sort(eigenvalues)[:k]
    
    elif method == "power":
        # Power method to find largest eigenvalue, then compute smallest
        # via shift: λ_min = λ_max - shift
        shift = np.trace(hessian_perp) / n  # Use mean as shift
        H_shifted = hessian_perp - shift * np.eye(n)
        
        # Power iteration for largest eigenvalue of shifted matrix
        v = np.random.rand(n)
        v = v / np.linalg.norm(v)
        
        for _ in range(100):
            Hv = H_shifted @ v
            v_new = Hv / np.linalg.norm(Hv)
            if np.abs(np.dot(v_new, v)) > 0.9999:
                break
            v = v_new
        
        lambda_max_shifted = np.dot(v, H_shifted @ v)
        eigenvalues = [shift + lambda_max_shifted]
    
    elif method == "lobpcg":
        #LOBPCG for large sparse matrices
        # Initialize with random vectors
        X = np.random.rand(n, min(k, n))
        X = X / np.linalg.norm(X, axis=0)
        
        try:
            if hessian_sparse is not None:
                eigenvalues, _ = lobpcg(hessian_sparse, X, maxiter=200)
            else:
                # Fallback to dense
                eigenvalues, _ = np.linalg.eigvalsh(hessian_perp)
                eigenvalues = np.sort(eigenvalues)[:k]
        except Exception:
            eigenvalues = np.linalg.eigvalsh(hessian_perp)
            eigenvalues = np.sort(eigenvalues)[:k]
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # κ₀ is the smallest eigenvalue
    kappa = np.min(eigenvalues)
    
    # Clamp to 0 (numerical errors may give tiny negatives)
    return max(0.0, kappa)


def compute_semantic_direction(
    state: np.ndarray,
    layout: "ASGStateLayout"
) -> np.ndarray:
    """Compute semantic direction v_sem = (0, G, -θ, 0)
    
    The semantic direction encodes the relationship:
    - Moving against gradients (-G) while changing angles (θ)
    - Represents "semantic stiffness" - how hard is it to move
      in the direction that changes meaning
    
    Args:
        state: Full state vector of shape (4N,)
        layout: State layout specification
        
    Returns:
        v_sem of shape (4N,)
    """
    N = layout.dimension
    
    # Extract blocks
    rho = state[layout.rho_start:layout.theta_start]
    theta = state[layout.theta_start:layout.gamma_start]
    gamma = state[layout.gamma_start:layout.zeta_start]
    zeta = state[layout.zeta_start:layout.total_dim]
    
    # Build semantic direction: (0, G, -θ, 0)
    v_sem = np.zeros(4 * N, dtype=np.float64)
    v_sem[layout.gamma_start:layout.zeta_start] = gamma  # G block
    v_sem[layout.theta_start:layout.gamma_start] = -theta  # -θ block
    
    return v_sem


def compute_semantic_rayleigh(
    hessian_perp: np.ndarray,
    v_sem: np.ndarray
) -> float:
    """Compute Γ_sem = (v_sem^T H_⊥ v_sem) / (v_sem^T v_sem)
    
    The semantic Rayleigh quotient measures stiffness in the semantic direction.
    This tells us how "hard" it is to change the system's semantic state.
    
    Args:
        hessian_perp: Projected Hessian H_⊥
        v_sem: Semantic direction vector
        
    Returns:
        Γ_sem - semantic stiffness
    """
    # Normalize semantic direction
    v_norm = np.linalg.norm(v_sem)
    if v_norm < 1e-10:
        return 0.0
    
    v_normalized = v_sem / v_norm
    
    # Rayleigh quotient: v^T H v / v^T v = (v_normalized^T H v_normalized)
    gamma_sem = v_normalized @ hessian_perp @ v_normalized
    
    return gamma_sem


def compute_margin(gamma_sem: float, kappa_0: float) -> float:
    """Compute M = Γ_sem / κ₀
    
    The semantic margin measures how much "room" we have in the semantic
    direction relative to the stiffness floor.
    
    Args:
        gamma_sem: Semantic stiffness Γ_sem
        kappa_0: Stiffness floor κ₀
        
    Returns:
        M - semantic margin
    """
    if kappa_0 < 1e-10:
        # Avoid division by zero
        return float('inf') if gamma_sem > 0 else 0.0
    
    return gamma_sem / kappa_0


def compute_spectral_certificate(
    hessian: np.ndarray,
    projector: np.ndarray,
    state: np.ndarray,
    layout: "ASGStateLayout",
    method: str = "eigsh"
) -> Tuple[float, float, float]:
    """Compute full spectral certificate: (κ₀, Γ_sem, M)
    
    Args:
        hessian: Full Hessian H
        projector: Mean-zero projector P_⊥
        state: State vector
        layout: State layout
        method: κ₀ estimation method
        
    Returns:
        Tuple of (kappa_0, gamma_sem, margin)
    """
    # Project Hessian
    hessian_perp = projector @ hessian @ projector
    
    # Estimate κ₀
    kappa_0 = estimate_kappa_0(hessian_perp, method=method)
    
    # Compute semantic direction
    v_sem = compute_semantic_direction(state, layout)
    v_sem_perp = projector @ v_sem  # Project semantic direction too
    
    # Compute Γ_sem
    gamma_sem = compute_semantic_rayleigh(hessian_perp, v_sem_perp)
    
    # Compute margin
    margin = compute_margin(gamma_sem, kappa_0)
    
    return kappa_0, gamma_sem, margin


def verify_stability_conditions(
    kappa_0: float,
    gamma_sem: float,
    margin: float,
    kappa_min: float = 1e-6,
    margin_min: float = 1.0
) -> dict:
    """Verify stability conditions for governance.
    
    Args:
        kappa_0: Estimated κ₀
        gamma_sem: Semantic stiffness
        margin: Semantic margin M
        kappa_min: Minimum required κ₀
        margin_min: Minimum required margin
        
    Returns:
        Dict with pass/fail for each condition
    """
    return {
        "kappa_positive": kappa_0 > 0,
        "kappa_adequate": kappa_0 >= kappa_min,
        "gamma_positive": gamma_sem > 0,
        "margin_adequate": margin >= margin_min,
        "all_passed": (
            kappa_0 >= kappa_min and 
            gamma_sem > 0 and 
            margin >= margin_min
        )
    }


def compute_condition_number(hessian_perp: np.ndarray) -> float:
    """Compute condition number κ(H_⊥) = λ_max / λ_min
    
    Args:
        hessian_perp: Projected Hessian
        
    Returns:
        Condition number (may be infinite if λ_min = 0)
    """
    eigenvalues = np.linalg.eigvalsh(hessian_perp)
    eigenvalues = np.sort(eigenvalues)
    
    lambda_min = max(0, eigenvalues[0])
    lambda_max = eigenvalues[-1]
    
    if lambda_min < 1e-10:
        return float('inf')
    
    return lambda_max / lambda_min
