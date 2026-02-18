# ASG Type Definitions

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ASGStateLayout:
    """State vector layout: u = (ρ, θ, G, ζ) ∈ R^{4N}
    
    The state is partitioned into four blocks:
    - ρ: linguistic/position variables
    - θ: angle variables (subject to mean-zero constraint)
    - G: gradient variables
    - ζ: auxiliary variables
    """
    rho_start: int       # ρ block start index (0)
    theta_start: int     # θ block start index (N)
    gamma_start: int     # G block start index (2N)
    zeta_start: int      # ζ block start index (3N)
    dimension: int        # N (system size, number of nodes)
    
    @property
    def total_dim(self) -> int:
        """Total state dimension = 4N"""
        return 4 * self.dimension
    
    @staticmethod
    def create_1d_ring(N: int) -> "ASGStateLayout":
        """Create layout for 1D ring with N nodes"""
        return ASGStateLayout(
            rho_start=0,
            theta_start=N,
            gamma_start=2*N,
            zeta_start=3*N,
            dimension=N,
        )
    
    @staticmethod
    def create_2d_torus(M: int, N: int) -> "ASGStateLayout":
        """Create layout for 2D torus with M×N nodes"""
        total_nodes = M * N
        return ASGStateLayout(
            rho_start=0,
            theta_start=total_nodes,
            gamma_start=2*total_nodes,
            zeta_start=3*total_nodes,
            dimension=total_nodes,
        )


@dataclass
class ASGParams:
    """ASG computation parameters"""
    state_layout: ASGStateLayout
    weights: List[float]
    alpha_l: float      # α_L: linguistic coupling strength
    alpha_g: float       # α_G: gradient coupling strength  
    w_theta: float       # w_θ: theta penalty weight
    
    def __post_init__(self):
        """Validate parameters"""
        if self.alpha_l < 0:
            raise ValueError("alpha_l must be non-negative")
        if self.alpha_g < 0:
            raise ValueError("alpha_g must be non-negative")
        if self.w_theta < 0:
            raise ValueError("w_theta must be non-negative")
        if len(self.weights) != self.state_layout.dimension:
            raise ValueError(
                f"weights length {len(self.weights)} must match "
                f"state dimension {self.state_layout.dimension}"
            )


@dataclass
class ASGReceipt:
    """Spectral certificate receipt
    
    Produced by ASG and consumed by NK-4G for audit.
    """
    kappa_est: float              # κ₀ = λ_min(H_⊥) estimate
    gamma_sem: float              # Γ_sem: semantic Rayleigh quotient
    semantic_margin: float        # M = Γ_sem / κ₀
    projector_id: str             # e.g., "mean_zero_theta_v1"
    operator_digest: str          # SHA-256 of operator structure
    estimation_method: str        # "eigsh", "lobpcg", "exact"
    state_hash: str               # Hash of input state
    params_hash: str              # Hash of ASG parameters
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "kappa_est": self.kappa_est,
            "gamma_sem": self.gamma_sem,
            "semantic_margin": self.semantic_margin,
            "projector_id": self.projector_id,
            "operator_digest": self.operator_digest,
            "estimation_method": self.estimation_method,
            "state_hash": self.state_hash,
            "params_hash": self.params_hash,
        }


@dataclass
class ResidualConfig:
    """Configuration for residual function r(u)"""
    residual_type: str            # "linguistic", "gradient", "orthogonal"
    node_indices: List[int]      # Which nodes this residual depends on
    coupling_strength: float      # Coupling coefficient
    
    def __post_init__(self):
        valid_types = ["linguistic", "gradient", "orthogonal", "angle_sum"]
        if self.residual_type not in valid_types:
            raise ValueError(f"residual_type must be one of {valid_types}")
