"""
CK-0 Scalar (Coherence Functional)

This module implements the canonical coherence measurement from CK-0 theory:

    C(x) = ⟨S⁻¹r(x), Σ⁻¹S⁻¹r(x)⟩

Where:
- r(x): Residual function (what got worse)
- S⁻¹: Inverse service map (normalization)
- Σ⁻¹: Inverse weighting matrix (prioritization)
- ⟨·,·⟩: Inner product (weighted combination)

The scalar C(x) measures the "coherence energy" of a state - how far
from equilibrium the system has drifted. This is the foundation for:
- PoC (Proof of Coherence) gates
- Bounded violation computation (Δ⁺)
- Governance cost calculation

References:
- docs/ck0/3_violation_functional.md
- docs/nec/3_delta_norms.md
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Protocol, Optional
from fractions import Fraction
from numbers import Number


class ResidualMap(Protocol):
    """Protocol for residual computation r(x)."""
    
    def __call__(self, state: Any) -> Any:
        """Compute residual r(x) for the state."""
        ...


class ServiceMap(Protocol):
    """Protocol for service map S (normalization)."""
    
    def __call__(self, x: Any) -> Any:
        """Apply service map S to argument."""
        ...
    
    def inverse(self, y: Any) -> Any:
        """Compute S⁻¹(y)."""
        ...


class WeightingMap(Protocol):
    """Protocol for weighting matrix Σ (prioritization)."""
    
    def __call__(self, x: Any) -> Any:
        """Apply weighting Σ to argument."""
        ...
    
    def inverse(self, y: Any) -> Any:
        """Compute Σ⁻¹(y)."""
        ...


@dataclass(frozen=True)
class CK0Scalar:
    """
    Canonical coherence scalar.
    
    Represents C(x) = ⟨S⁻¹r(x), Σ⁻¹S⁻¹r(x)⟩ decomposed into components.
    
    Attributes:
        residual: S⁻¹r(x) - service-normalized residual
        weighted: Σ⁻¹S⁻¹r(x) - priority-weighted residual  
        total: ⟨residual, weighted⟩ - inner product (total coherence energy)
    """
    
    residual: Fraction
    weighted: Fraction
    total: Fraction
    
    def is_admissible(self, eps0: Fraction = Fraction(0)) -> bool:
        """
        Check if state is admissible (C(x) ≤ ε₀).
        
        Args:
            eps0: Tolerance threshold (default 0.0)
            
        Returns:
            True if total coherence energy is within tolerance
        """
        return self.total <= eps0
    
    def delta_plus(self, other: CK0Scalar) -> Fraction:
        """
        Compute Δ⁺ = max(0, C(x') - C(x)).
        
        This is the excess violation - how much the coherence
        energy increased from one state to another.
        
        Args:
            other: The target state scalar (x')
            
        Returns:
            The excess violation (always non-negative)
        """
        diff = other.total - self.total
        return Fraction(max(0, diff))


def compute_ck0_scalar(
    state: Any,
    residual_fn: Callable[[Any], Any],
    service_map: Optional[ServiceMap] = None,
    weighting_map: Optional[WeightingMap] = None,
    inner_product: Optional[Callable[[Any, Any], Fraction]] = None,
) -> CK0Scalar:
    """
    Compute C(x) = ⟨S⁻¹r(x), Σ⁻¹S⁻¹r(x)⟩ for a given state.
    
    This is the canonical coherence measurement function.
    
    Args:
        state: The state x to measure
        residual_fn: Residual function r(x)
        service_map: Service map S (if None, identity is used)
        weighting_map: Weighting matrix Σ (if None, identity is used)
        inner_product: Inner product function (if None, multiplication is used)
    
    Returns:
        CK0Scalar with residual, weighted, and total components
        
    Example:
        >>> def r(x): return x - x_equilibrium
        >>> scalar = compute_ck0_scalar(current_state, r)
        >>> if scalar.is_admissible():
        ...     print("State is coherent")
    """
    # Step 1: Compute residual r(x)
    residual_raw = residual_fn(state)
    
    # Convert to Fraction if numeric
    if isinstance(residual_raw, Number):
        residual_raw = Fraction(residual_raw)
    
    # Step 2: Apply S⁻¹ (service normalization)
    if service_map is not None and hasattr(service_map, 'inverse'):
        service_normalized = service_map.inverse(residual_raw)
    else:
        service_normalized = residual_raw  # Identity
    
    if isinstance(service_normalized, Number):
        service_normalized = Fraction(service_normalized)
    
    # Step 3: Apply Σ⁻¹ (weighting)
    if weighting_map is not None and hasattr(weighting_map, 'inverse'):
        weighted = weighting_map.inverse(service_normalized)
    else:
        weighted = service_normalized  # Identity
    
    if isinstance(weighted, Number):
        weighted = Fraction(weighted)
    
    # Step 4: Compute inner product ⟨service_normalized, weighted⟩
    if inner_product is not None:
        total = inner_product(service_normalized, weighted)
    else:
        # Default: scalar multiplication
        total = service_normalized * weighted
    
    if isinstance(total, Number):
        total = Fraction(total)
    
    return CK0Scalar(
        residual=Fraction(service_normalized),
        weighted=Fraction(weighted),
        total=Fraction(total)
    )


def delta_plus(
    scalar_before: CK0Scalar,
    scalar_after: CK0Scalar
) -> Fraction:
    """
    Compute Δ⁺ = max(0, C(x') - C(x)).
    
    This is the excess violation - the amount by which coherence
    energy increased. This is the key quantity that determines
    governance cost under Regime B.
    
    Args:
        scalar_before: C(x) - coherence of pre-state
        scalar_after: C(x') - coherence of post-state
        
    Returns:
        The excess violation (always non-negative)
        
    Note:
        Under strict PoC (Regime A), any Δ⁺ > 0 would cause rejection.
        Under bounded PoC (Regime B), Δ⁺ triggers proportional cost.
    """
    return scalar_before.delta_plus(scalar_after)


# =============================================================================
# Common Service/Weighting Implementations
# =============================================================================

class IdentityServiceMap:
    """Identity service map: S(x) = x, S⁻¹(x) = x."""
    
    def __call__(self, x: Any) -> Any:
        return x
    
    def inverse(self, x: Any) -> Any:
        return x


class ScalingServiceMap:
    """Scaling service map: S(x) = scale * x, S⁻¹(x) = x / scale."""
    
    def __init__(self, scale: Fraction = Fraction(1)):
        self.scale = Fraction(scale)
    
    def __call__(self, x: Any) -> Any:
        if isinstance(x, Number):
            return x * self.scale
        return x
    
    def inverse(self, x: Any) -> Any:
        if isinstance(x, Number):
            return x / self.scale
        return x


class ClampServiceMap:
    """Clamped service map: S⁻¹(x) = clamp(x, min_val, max_val)."""
    
    def __init__(
        self, 
        min_val: Fraction = Fraction(0), 
        max_val: Fraction = Fraction(10**18)
    ):
        self.min_val = Fraction(min_val)
        self.max_val = Fraction(max_val)
    
    def inverse(self, x: Any) -> Fraction:
        if isinstance(x, Number):
            x = Fraction(x)
            return max(self.min_val, min(self.max_val, x))
        return x


class DiagonalWeighting:
    """Diagonal weighting matrix: Σ(x) = weight * x."""
    
    def __init__(self, weight: Fraction = Fraction(1)):
        self.weight = Fraction(weight)
    
    def __call__(self, x: Any) -> Any:
        if isinstance(x, Number):
            return x * self.weight
        return x
    
    def inverse(self, x: Any) -> Any:
        if isinstance(x, Number):
            return x / self.weight
        return x


# =============================================================================
# Convenience Functions
# =============================================================================

def simple_ck0_scalar(
    state_value: Number,
    equilibrium: Number = 0,
    scale: Fraction = Fraction(1),
    weight: Fraction = Fraction(1)
) -> CK0Scalar:
    """
    Simplified CK-0 scalar for scalar state values.
    
    Args:
        state_value: The actual state value x
        equilibrium: The equilibrium value (default 0)
        scale: Service scaling factor
        weight: Weighting factor
        
    Returns:
        CK0Scalar for the state
        
    Example:
        >>> scalar = simple_ck0_scalar(0.5, equilibrium=0.0)
        >>> print(f"C(x) = {scalar.total}")
    """
    # Residual: deviation from equilibrium
    residual = state_value - equilibrium
    
    # S⁻¹: scale
    service_normalized = residual * scale
    
    # Σ⁻¹: weight  
    weighted = service_normalized * weight
    
    # Inner product: multiplication
    total = service_normalized * weighted
    
    return CK0Scalar(
        residual=Fraction(service_normalized),
        weighted=Fraction(weighted),
        total=Fraction(total)
    )
