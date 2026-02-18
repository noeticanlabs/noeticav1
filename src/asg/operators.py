# ASG Operators - Gradient and Projection Operators

import numpy as np
from typing import Tuple


def build_gradient_operator_1d_ring(N: int) -> np.ndarray:
    """Build discrete gradient operator for 1D ring topology.
    
    The gradient operator D computes discrete differences between adjacent nodes
    in a ring (periodic boundary conditions).
    
    D[i,j] = 1 if j = i+1 (mod N)
           = -1 if j = i-1 (mod N)
           = 0 otherwise
    
    Args:
        N: Number of nodes in the ring
        
    Returns:
        D matrix of shape (N, N)
    """
    D = np.zeros((N, N), dtype=np.float64)
    
    for i in range(N):
        # Forward difference: node (i+1) - node i
        D[i, i] = -1
        D[i, (i + 1) % N] = 1
    
    return D


def build_gradient_operator_2d_torus(M: int, N: int) -> np.ndarray:
    """Build discrete gradient operator for 2D torus topology.
    
    The gradient operator computes differences in both row and column directions
    for an M×N grid with periodic boundary conditions.
    
    Args:
        M: Number of rows
        N: Number of columns
        
    Returns:
        D matrix of shape (2*M*N, M*N) where first M*N rows are row gradients
        and last M*N rows are column gradients
    """
    total_nodes = M * N
    D = np.zeros((2 * total_nodes, total_nodes), dtype=np.float64)
    
    for i in range(M):
        for j in range(N):
            idx = i * N + j
            
            # Row direction gradient (i+1, j) - (i, j)
            row_idx = idx
            D[row_idx, idx] = -1
            D[row_idx, ((i + 1) % M) * N + j] = 1
            
            # Column direction gradient (i, j+1) - (i, j)
            col_idx = total_nodes + idx
            D[col_idx, idx] = -1
            D[col_idx, i * N + ((j + 1) % N)] = 1
    
    return D


def build_mean_zero_projector(dimension: int) -> np.ndarray:
    """Build P_⊥ = I - (1/N) 11^T that removes mean(theta) mode.
    
    This projector enforces the constraint Σ θ_i = 0 by projecting onto
    the subspace orthogonal to the all-ones vector.
    
    P_⊥ v = v - mean(v) * 1
    
    Args:
        dimension: N (number of elements)
        
    Returns:
        P_⊥ matrix of shape (N, N)
    """
    ones = np.ones(dimension)
    P_perp = np.eye(dimension) - np.outer(ones, ones) / dimension
    return P_perp


def build_laplacian_1d_ring(N: int) -> np.ndarray:
    """Build 1D ring Laplacian: L = D^T D
    
    The Laplacian computes the second-order finite difference.
    
    Args:
        N: Number of nodes
        
    Returns:
        L matrix of shape (N, N)
    """
    D = build_gradient_operator_1d_ring(N)
    L = D.T @ D
    return L


def build_laplacian_2d_torus(M: int, N: int) -> np.ndarray:
    """Build 2D torus Laplacian: L = D^T D
    
    Args:
        M: Number of rows
        N: Number of columns
        
    Returns:
        L matrix of shape (M*N, M*N)
    """
    D = build_gradient_operator_2d_torus(M, N)
    L = D.T @ D
    return L


def build_diagonal_weight_matrix(weights: np.ndarray) -> np.ndarray:
    """Build diagonal weight matrix from weight vector.
    
    Args:
        weights: Array of shape (N,) with weights for each node
        
    Returns:
        W matrix of shape (N, N) - diagonal matrix
    """
    return np.diag(weights)


def compute_state_blocks(
    state: np.ndarray, 
    layout: "ASGStateLayout"
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract state blocks (ρ, θ, G, ζ) from flat state vector.
    
    Args:
        state: Flat state vector of shape (4N,)
        layout: State layout specification
        
    Returns:
        Tuple of (rho, theta, gamma, zeta) arrays
    """
    N = layout.dimension
    rho = state[layout.rho_start:layout.theta_start]
    theta = state[layout.theta_start:layout.gamma_start]
    gamma = state[layout.gamma_start:layout.zeta_start]
    zeta = state[layout.zeta_start:layout.total_dim]
    return rho, theta, gamma, zeta


def assemble_state_vector(
    rho: np.ndarray,
    theta: np.ndarray,
    gamma: np.ndarray,
    zeta: np.ndarray
) -> np.ndarray:
    """Assemble state blocks into flat state vector.
    
    Args:
        rho: Linguistic/position variables
        theta: Angle variables
        gamma: Gradient variables
        zeta: Auxiliary variables
        
    Returns:
        Flat state vector of shape (4N,)
    """
    return np.concatenate([rho, theta, gamma, zeta])


def apply_projector_to_theta(
    theta: np.ndarray,
    projector: np.ndarray
) -> np.ndarray:
    """Apply mean-zero projector to theta block.
    
    Args:
        theta: Angle variables of shape (N,)
        projector: Mean-zero projector of shape (N, N)
        
    Returns:
        Projected theta with zero mean
    """
    return projector @ theta


def compute_theta_mean(theta: np.ndarray) -> float:
    """Compute mean of theta vector.
    
    Args:
        theta: Angle variables
        
    Returns:
        Mean value
    """
    return np.mean(theta)


def compute_theta_sum(theta: np.ndarray) -> float:
    """Compute sum of theta vector.
    
    Args:
        theta: Angle variables
        
    Returns:
        Sum value
    """
    return np.sum(theta)
