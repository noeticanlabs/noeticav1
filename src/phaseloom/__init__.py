# PhaseLoom Potential — Geometric Memory
#
# Canon Doc Spine v1.0.0
# Scope: CK-0 / (Coh) + PhaseLoom Endofunctor + Fixed-Point Receipt Protocol + STF/LoomVerifier
# Layer: L2 (Control & Time Geometry) projecting into L4 (Runtime) and L5 (Proof)

"""
PhaseLoom Potential Module

This module implements the PhaseLoom construction that:
1. Extends the state space from X to X × M (geometric memory)
2. Defines the PhaseLoom Potential V_PL as an extended Lyapunov functional
3. Enforces curvature-bounded viability via multi-clock interlock
4. Provides cryptographically verifiable transitions via receipts
5. Resolves safety vs liveness via Authority Injection

Submodules:
- types: Core type definitions (PLState, Params, etc.)
- functor: PhaseLoom endofunctor implementation
- curvature: Curvature accumulator C
- tension: Tension accumulator T
- potential: PhaseLoom Potential V_PL
- interlock: Scheduler interlock
- authority: Authority injection
- receipt: Receipt contract v1
- verifier: LoomVerifier STF
- compression: Slab compression
"""

__version__ = "phaseloom_potential_geometric_memory_v1.0.0"

# Version compatibility
COMPAT_CK0 = "ck0.v1"
COMPAT_COH = "coh.v1"
COMPAT_NK1 = "nk1.v1"
COMPAT_NK2 = "nk2.v1"

# Re-export main types
from .types import (
    PLState,
    PLParams,
    MemoryState,
    FixedPoint,
    StepType,
    Weights,
)

from .functor import PhaseLoomFunctor

from .potential import compute_potential

from .interlock import check_interlock, admissible_steps

from .verifier import LoomVerifier

__all__ = [
    "__version__",
    # Types
    "PLState",
    "PLParams", 
    "MemoryState",
    "FixedPoint",
    "StepType",
    "Weights",
    # Functor
    "PhaseLoomFunctor",
    # Core functions
    "compute_potential",
    "check_interlock",
    "admissible_steps",
    # Verifier
    "LoomVerifier",
]
