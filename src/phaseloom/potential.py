# PhaseLoom Potential — Extended Lyapunov Functional
#
# Implements V_PL computation as per canon spine

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .types import (
    PLState,
    PLParams,
    FixedPoint,
    Weights,
)


def barrier(b: FixedPoint, epsilon: FixedPoint) -> FixedPoint:
    """Compute barrier function: ψ(b) = 1 / (b + ε)
    
    Properties:
    - Strictly decreasing in b
    - Blows up as b → 0+
    - Bounded as b → ∞
    
    Args:
        b: Budget value
        epsilon: Small constant to avoid division by zero
        
    Returns:
        ψ(b)
        
    Raises:
        ZeroDivisionError: If b + epsilon = 0 (should not happen with epsilon > 0)
    """
    denominator = b + epsilon
    if denominator.value == 0:
        raise ZeroDivisionError("Barrier denominator cannot be zero")
    
    # Compute 1 / (b + ε)
    # Using fixed-point: 1 / x = SCALE_FACTOR / x
    return FixedPoint.one() / denominator


def compute_potential(
    V: FixedPoint,
    C: FixedPoint,
    T: FixedPoint,
    b: FixedPoint,
    a: FixedPoint,
    weights: Weights,
    epsilon: FixedPoint
) -> FixedPoint:
    """Compute PhaseLoom Potential V_PL.
    
    V_PL = w_0 * V + w_C * max(C, 0) + w_T * T + w_b * ψ(b) + w_a * a
    
    Args:
        V: Base violation functional value
        C: Curvature (will be clamped to non-negative)
        T: Tension
        b: Budget
        a: Authority
        weights: Weight parameters
        epsilon: Barrier constant
        
    Returns:
        V_PL value
    """
    # Curvature penalty (only positive curvature)
    C_penalty = C if C.value >= 0 else FixedPoint.zero()
    
    # Barrier term
    barrier_term = barrier(b, epsilon)
    
    # Compute weighted sum
    return (
        weights.w0 * V +
        weights.wC * C_penalty +
        weights.wT * T +
        weights.wb * barrier_term +
        weights.wa * a
    )


def compute_potential_from_state(
    state: PLState,
    params: PLParams
) -> FixedPoint:
    """Compute V_PL from PLState.
    
    Args:
        state: PhaseLoom state
        params: Governance parameters
        
    Returns:
        V_PL value
    """
    return compute_potential(
        V=FixedPoint.zero(),  # Would be V(x) from CK-0
        C=state.C,
        T=state.T,
        b=state.b,
        a=state.a,
        weights=params.weights,
        epsilon=params.epsilon
    )


def compute_potential_delta(
    prev_state: PLState,
    next_state: PLState,
    params: PLParams,
    delta_V: FixedPoint  # V(x^+) - V(x)
) -> FixedPoint:
    """Compute change in potential between states.
    
    ΔV_PL = V_PL(x^+) - V_PL(x)
    
    Args:
        prev_state: Previous state
        next_state: Next state
        params: Governance parameters
        delta_V: Change in base violation
        
    Returns:
        ΔV_PL
    """
    prev_V_PL = compute_potential_from_state(prev_state, params)
    
    # For next state, we need V(x^+)
    # In practice this comes from CK-0
    # Here we compute with the delta
    next_V = delta_V  # This is simplified
    
    # Compute next potential (V would come from actual CK-0)
    # For now, return the difference
    return prev_V_PL  # Placeholder - actual implementation needs V from CK-0


@dataclass
class PotentialBounds:
    """Bounds on potential values."""
    min_V_PL: FixedPoint
    max_V_PL: FixedPoint
    budget_exhaustion: FixedPoint  # Potential when b = 0
    
    @classmethod
    def compute(
        cls,
        max_V: FixedPoint,
        max_C: FixedPoint,
        max_T: FixedPoint,
        b_init: FixedPoint,
        a_init: FixedPoint,
        params: PLParams
    ) -> PotentialBounds:
        """Compute potential bounds from max values."""
        # Max potential (when b = epsilon)
        max_potential = compute_potential(
            V=max_V,
            C=max_C,
            T=max_T,
            b=params.epsilon,  # Near zero budget
            a=a_init,
            weights=params.weights,
            epsilon=params.epsilon
        )
        
        # Min potential (when b is large)
        min_potential = compute_potential(
            V=FixedPoint.zero(),
            C=FixedPoint.zero(),
            T=FixedPoint.zero(),
            b=b_init,
            a=FixedPoint.zero(),
            weights=params.weights,
            epsilon=params.epsilon
        )
        
        # Budget exhaustion potential
        budget_exhaustion = compute_potential(
            V=max_V,
            C=max_C,
            T=max_T,
            b=FixedPoint.zero(),
            a=a_init,
            weights=params.weights,
            epsilon=params.epsilon
        )
        
        return cls(
            min_V_PL=min_potential,
            max_V_PL=max_potential,
            budget_exhaustion=budget_exhaustion
        )
