# PhaseLoom Curvature Accumulator
#
# Implements C recurrence as per canon spine Section 5

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

from .types import FixedPoint


def compute_amplification(delta_v: FixedPoint) -> FixedPoint:
    """Compute amplification: A = (Δv)+ = max(Δv, 0)
    
    Args:
        delta_v: Violation change V(x+) - V(x)
        
    Returns:
        Amplification (non-negative)
    """
    return FixedPoint(max(delta_v.value, 0))


def compute_dissipation(delta_v: FixedPoint) -> FixedPoint:
    """Compute dissipation: D = (-Δv)+ = max(-Δv, 0)
    
    Args:
        delta_v: Violation change V(x+) - V(x)
        
    Returns:
        Dissipation (non-negative)
    """
    return FixedPoint(max(-delta_v.value, 0))


def compute_curvature_next(
    C: FixedPoint,
    A: FixedPoint,
    D: FixedPoint,
    rho_C: FixedPoint
) -> FixedPoint:
    """Compute next curvature: C+ = ρ_C * C + (A - D)
    
    Then clamp to non-negative: C+ = max(C+, 0)
    
    Args:
        C: Current curvature
        A: Amplification
        D: Dissipation
        rho_C: Decay factor in [0, 1)
        
    Returns:
        Next curvature (non-negative)
    """
    # Compute raw curvature
    raw = rho_C * C + (A - D)
    
    # Clamp to non-negative
    return FixedPoint(max(raw.value, 0))


def compute_curvature_penalty(C: FixedPoint) -> FixedPoint:
    """Compute curvature penalty: max(C, 0)
    
    Only positive curvature contributes to potential.
    
    Args:
        C: Curvature value
        
    Returns:
        Penalty (non-negative)
    """
    return FixedPoint(max(C.value, 0))


@dataclass
class CurvatureState:
    """Curvature accumulator state."""
    C: FixedPoint
    A: FixedPoint  # Amplification from last step
    D: FixedPoint  # Dissipation from last step
    
    @classmethod
    def zero(cls) -> 'CurvatureState':
        return cls(
            C=FixedPoint.zero(),
            A=FixedPoint.zero(),
            D=FixedPoint.zero()
        )


class CurvatureAccumulator:
    """Curvature accumulator for PhaseLoom.
    
    Tracks net amplification over dissipation using exponential decay.
    """
    
    def __init__(self, rho_C: FixedPoint):
        """Initialize with decay factor.
        
        Args:
            rho_C: Decay factor in [0, 1)
        """
        self.rho_C = rho_C
    
    def update(
        self,
        state: CurvatureState,
        delta_v: FixedPoint
    ) -> CurvatureState:
        """Update curvature from violation change.
        
        Args:
            state: Current curvature state
            delta_v: Violation change V(x+) - V(x)
            
        Returns:
            Updated curvature state
        """
        # Compute amp/diss
        A = compute_amplification(delta_v)
        D = compute_dissipation(delta_v)
        
        # Compute next curvature
        C_next = compute_curvature_next(state.C, A, D, self.rho_C)
        
        return CurvatureState(C=C_next, A=A, D=D)
    
    def verify_recurrence(
        self,
        C_prev: FixedPoint,
        C_next: FixedPoint,
        A: FixedPoint,
        D: FixedPoint
    ) -> bool:
        """Verify curvature recurrence holds.
        
        Args:
            C_prev: Previous curvature
            C_next: Next curvature  
            A: Amplification
            D: Dissipation
            
        Returns:
            True if recurrence holds
        """
        expected = compute_curvature_next(C_prev, A, D, self.rho_C)
        return C_next == expected


def decompose_delta(delta_v: FixedPoint) -> Tuple[FixedPoint, FixedPoint]:
    """Decompose violation change into amplification and dissipation.
    
    Δv = A - D
    A * D = 0 (mutually exclusive)
    
    Args:
        delta_v: Violation change
        
    Returns:
        Tuple of (A, D)
    """
    A = compute_amplification(delta_v)
    D = compute_dissipation(delta_v)
    return (A, D)
