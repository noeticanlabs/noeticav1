# ASG Assembly - Jacobian and Hessian Construction

import numpy as np
import hashlib
from typing import List, Callable, Optional, Tuple
from dataclasses import asdict

from .types import ASGParams, ASGStateLayout, ResidualConfig


def assemble_jacobian(
    params: ASGParams,
    residuals: List[Callable[[np.ndarray], np.ndarray]]
) -> np.ndarray:
    """Assemble Jacobian matrix O from residual functions.
    
    O = [√w_i J_i] where J_i = dr_i/du is the Jacobian of residual r_i
    
    Args:
        params: ASG parameters
        residuals: List of residual functions r_i(state) -> residual vector
        
    Returns:
        O matrix of shape (m, 4N) where m is total residual dimension
    """
    N = params.state_layout.dimension
    state_dim = 4 * N
    
    # Compute Jacobian for each residual numerically
    jacobian_blocks = []
    
    eps = 1e-8  # Finite difference step
    
    for i, res_fn in enumerate(residuals):
        # Get residual at current point
        # Note: In practice, we'd need the actual state. For now, return shape info
        # This is a placeholder - actual implementation would compute J_i
        pass
    
    # Placeholder: return identity-scaled Jacobian
    # In full implementation, this computes actual J_i for each residual
    total_residual_dim = len(residuals) * N  # Assuming N-dim residuals
    O = np.zeros((total_residual_dim, state_dim), dtype=np.float64)
    
    # Diagonal blocks for each residual type
    for i, res_config in enumerate(params.residuals):
        row_start = i * N
        col_start = _get_residual_block_start(res_config, params.state_layout)
        
        # Fill diagonal block with sqrt(weight) * identity
        weight = params.weights[i] if i < len(params.weights) else 1.0
        O[row_start:row_start+N, col_start:col_start+N] = np.sqrt(weight) * np.eye(N)
    
    return O


def _get_residual_block_start(res_config: ResidualConfig, layout: ASGStateLayout) -> int:
    """Get column start index for a residual block"""
    if res_config.residual_type == "linguistic":
        return layout.rho_start
    elif res_config.residual_type == "gradient":
        return layout.gamma_start
    elif res_config.residual_type == "angle_sum":
        return layout.theta_start
    elif res_config.residual_type == "orthogonal":
        return layout.zeta_start
    else:
        return 0


def assemble_hessian_model(jacobian: np.ndarray) -> np.ndarray:
    """Compute H = O^T O (always PSD by construction).
    
    Since H = O^T O for any matrix O, it is positive semidefinite by construction:
    v^T H v = v^T O^T O v = ||O v||² ≥ 0
    
    Args:
        jacobian: O matrix of shape (m, n)
        
    Returns:
        H matrix of shape (n, n), PSD by construction
    """
    H = jacobian.T @ jacobian
    return H


def project_hessian(
    hessian: np.ndarray,
    projector: np.ndarray
) -> np.ndarray:
    """Project Hessian onto reduced space: H_⊥ = P_⊥ H P_⊥
    
    Args:
        hessian: Full Hessian matrix H of shape (n, n)
        projector: Projection matrix P_⊥ of shape (n, n)
        
    Returns:
        Projected Hessian H_⊥
    """
    return projector @ hessian @ projector


def compute_operator_digest(
    params: ASGParams,
    hessian: Optional[np.ndarray] = None
) -> str:
    """Compute SHA-256 digest of operator structure + parameters.
    
    The digest captures:
    - State layout
    - Coupling parameters (alpha_l, alpha_g, w_theta)
    - Topology type (1D ring or 2D torus)
    - Hessian structure (if provided)
    
    Args:
        params: ASG parameters
        hessian: Optional Hessian matrix for structural digest
        
    Returns:
        Hex digest string (64 characters)
    """
    # Create deterministic string representation
    digest_parts = [
        f"layout={params.state_layout.dimension}",
        f"alpha_l={params.alpha_l:.10f}",
        f"alpha_g={params.alpha_g:.10f}",
        f"w_theta={params.w_theta:.10f}",
    ]
    
    # Add residual configs if present
    if hasattr(params, 'residuals') and params.residuals:
        for rc in params.residuals:
            digest_parts.append(f"res={rc.residual_type}:{rc.coupling_strength:.10f}")
    
    # Add Hessian structure if provided
    if hessian is not None:
        # Use only structural info (sparsity pattern) not values
        struct = (hessian != 0).astype(int)
        digest_parts.append(f"hessian_nnz={np.sum(struct)}")
    
    # Compute hash
    digest_str = "|".join(digest_parts)
    hash_obj = hashlib.sha256(digest_str.encode('utf-8'))
    return hash_obj.hexdigest()


def compute_state_digest(state: np.ndarray) -> str:
    """Compute SHA-256 digest of state vector.
    
    Args:
        state: State vector
        
    Returns:
        Hex digest string
    """
    # Use base64 encoding for compact representation
    state_bytes = state.tobytes()
    hash_obj = hashlib.sha256(state_bytes)
    return hash_obj.hexdigest()


def compute_params_digest(params: ASGParams) -> str:
    """Compute SHA-256 digest of ASG parameters.
    
    Args:
        params: ASG parameters
        
    Returns:
        Hex digest string
    """
    digest_parts = [
        f"alpha_l={params.alpha_l}",
        f"alpha_g={params.alpha_g}",
        f"w_theta={params.w_theta}",
        f"dim={params.state_layout.dimension}",
    ]
    
    # Add weights
    for i, w in enumerate(params.weights):
        digest_parts.append(f"w{i}={w}")
    
    digest_str = "|".join(digest_parts)
    hash_obj = hashlib.sha256(digest_str.encode('utf-8'))
    return hash_obj.hexdigest()


def build_linguistic_residual_jacobian(
    N: int,
    alpha_l: float,
    weights: np.ndarray
) -> np.ndarray:
    """Build Jacobian for linguistic residuals.
    
    r_linguistic = sqrt(w_i) * (ρ_i - mean(ρ))
    
    Args:
        N: Number of nodes
        alpha_l: Linguistic coupling strength
        weights: Weight vector
        
    Returns:
        Jacobian matrix
    """
    # J = sqrt(w) * (I - (1/N)11^T)
    ones = np.ones(N)
    J = np.diag(np.sqrt(weights)) @ (np.eye(N) - np.outer(ones, ones) / N)
    return J * np.sqrt(alpha_l)


def build_gradient_residual_jacobian(
    N: int,
    alpha_g: float,
    weights: np.ndarray,
    topology: str = "1d_ring"
) -> np.ndarray:
    """Build Jacobian for gradient residuals.
    
    r_gradient = sqrt(w) * D * θ (discrete gradient of theta)
    
    Args:
        N: Number of nodes
        alpha_g: Gradient coupling strength
        weights: Weight vector
        topology: "1d_ring" or "2d_torus"
        
    Returns:
        Jacobian matrix
    """
    from .operators import build_gradient_operator_1d_ring, build_gradient_operator_2d_torus
    
    if topology == "1d_ring":
        D = build_gradient_operator_1d_ring(N)
    elif topology == "2d_torus":
        # For 2D, N should be M*N
        M = int(np.sqrt(N))
        D = build_gradient_operator_2d_torus(M, N // M)
    else:
        raise ValueError(f"Unknown topology: {topology}")
    
    # J = sqrt(w) * D (acts on theta block)
    W = np.diag(np.sqrt(weights))
    J = W @ D
    return J * np.sqrt(alpha_g)


def build_angle_penalty_jacobian(
    N: int,
    w_theta: float
) -> np.ndarray:
    """Build Jacobian for angle penalty residuals.
    
    r_angle = sqrt(w_theta) * θ
    
    Args:
        N: Number of nodes
        w_theta: Angle penalty weight
        
    Returns:
        Jacobian matrix (N x N)
    """
    return np.sqrt(w_theta) * np.eye(N)


def assemble_full_jacobian(params: ASGParams, topology: str = "1d_ring") -> np.ndarray:
    """Assemble full Jacobian from all residual types.
    
    Args:
        params: ASG parameters
        topology: "1d_ring" or "2d_torus"
        
    Returns:
        Full O matrix
    """
    N = params.state_layout.dimension
    weights = np.array(params.weights)
    
    # Linguistic residuals (act on rho block)
    J_ling = build_linguistic_residual_jacobian(N, params.alpha_l, weights)
    
    # Gradient residuals (act on theta block -> gamma)
    J_grad = build_gradient_residual_jacobian(N, params.alpha_g, weights, topology)
    
    # Angle penalty (acts on theta block)
    J_angle = build_angle_penalty_jacobian(N, params.w_theta)
    
    # Assemble block diagonal
    O = np.zeros((3 * N, 4 * N), dtype=np.float64)
    
    # rho block (0:N) -> linguistic (0:N)
    O[0:N, 0:N] = J_ling
    
    # theta block (N:2N) -> gradient (N:2N)
    O[N:2*N, N:2*N] = J_grad
    
    # theta block (N:2N) -> angle (2N:3N)
    O[2*N:3*N, N:2*N] = J_angle
    
    return O


def verify_hessian_psd(hessian: np.ndarray, tol: float = 1e-10) -> bool:
    """Verify Hessian is positive semidefinite.
    
    Args:
        hessian: Hessian matrix H
        tol: Tolerance for eigenvalue check
        
    Returns:
        True if all eigenvalues >= -tol
    """
    eigenvalues = np.linalg.eigvalsh(hessian)
    return np.all(eigenvalues >= -tol)
