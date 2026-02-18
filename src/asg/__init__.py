# ASG - Adaptive Spectral Governance
"""
ASG provides computable curvature models for CK-0 residual architectures
and produces spectral certificates consumed by NK-4G.

Core responsibilities:
- Assemble residual Jacobian O and Hessian model H = O^T O
- Compute spectral quantities: κ₀, Γ_sem, margin M
- Emit watchdog receipts for prox inequality verification
"""

from .types import ASGStateLayout, ASGParams, ASGReceipt
from .operators import (
    build_gradient_operator_1d_ring,
    build_gradient_operator_2d_torus,
    build_mean_zero_projector,
)
from .assembly import assemble_jacobian, assemble_hessian_model, compute_operator_digest
from .spectral import (
    estimate_kappa_0,
    compute_semantic_direction,
    compute_semantic_rayleigh,
    compute_margin,
)
from .watchdog import ProxWatchdog

__all__ = [
    "ASGStateLayout",
    "ASGParams",
    "ASGReceipt",
    "build_gradient_operator_1d_ring",
    "build_gradient_operator_2d_torus",
    "build_mean_zero_projector",
    "assemble_jacobian",
    "assemble_hessian_model",
    "compute_operator_digest",
    "estimate_kappa_0",
    "compute_semantic_direction",
    "compute_semantic_rayleigh",
    "compute_margin",
    "ProxWatchdog",
]
