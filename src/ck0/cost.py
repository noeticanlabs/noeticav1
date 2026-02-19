"""
Governance Cost Functions

This module implements the Regime B (bounded violation) cost model:

    verification_cost(f) = base_fee + λ * Δ⁺ + penalties

Where:
- base_fee: Fixed verification overhead (often 0 for coherent steps)
- λ: Global governance stiffness (protocol constant)
- Δ⁺: max(0, C(x') - C(x)) - excess violation
- penalties: Policy-specific penalty amounts

This implements the oplax proof functor:

    |f|_V = inf(π) | spent(π) such that V(desc(f), π) = Accept

Under Regime B, we use deterministic cost extraction instead of infimum.

Key properties:
- Subadditivity: |g ∘ f| ≤ |f| + |g| (compositionality)
- Global λ ensures compositionality guarantees
- Contract-level variation only via CK-0 weights/bounds, not λ

References:
- plans/coh_structural_audit_implementation_plan.md
- docs/ck0/4_budget_debt_law.md
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from fractions import Fraction
from numbers import Number

# Global governance stiffness (protocol constant)
# This is fixed to guarantee compositionality
LAMBDA_GLOBAL: Fraction = Fraction(1)


@dataclass(frozen=True)
class CostConfig:
    """
    Configuration for governance cost computation.
    
    Attributes:
        base_fee: Fixed verification overhead (default 0)
        lambda_global: Governance stiffness λ (default 1)
        delta_max: Maximum allowed Δ⁺ (None = unbounded)
        penalties: Dict of policy_name -> penalty amount
    """
    
    base_fee: Fraction = Fraction(0)
    lambda_global: Fraction = LAMBDA_GLOBAL
    delta_max: Optional[Fraction] = None
    penalties: tuple = field(default_factory=tuple)  # Immutable
    
    def __post_init__(self):
        """Validate configuration."""
        if self.lambda_global < 0:
            raise ValueError("λ must be non-negative")
        if self.delta_max is not None and self.delta_max < 0:
            raise ValueError("delta_max must be non-negative")
    
    def get_penalty(self, policy_name: str) -> Fraction:
        """Get penalty for a policy name."""
        for name, amount in self.penalties:
            if name == policy_name:
                return amount
        return Fraction(0)
    
    def with_base_fee(self, base_fee: Fraction) -> CostConfig:
        """Create new config with different base_fee."""
        return CostConfig(
            base_fee=base_fee,
            lambda_global=self.lambda_global,
            delta_max=self.delta_max,
            penalties=self.penalties
        )
    
    def with_lambda(self, lambda_val: Fraction) -> CostConfig:
        """Create new config with different λ."""
        return CostConfig(
            base_fee=self.base_fee,
            lambda_global=lambda_val,
            delta_max=self.delta_max,
            penalties=self.penalties
        )
    
    def with_delta_max(self, delta_max: Optional[Fraction]) -> CostConfig:
        """Create new config with different delta_max."""
        return CostConfig(
            base_fee=self.base_fee,
            lambda_global=self.lambda_global,
            delta_max=delta_max,
            penalties=self.penalties
        )


def verification_cost(
    delta_plus: Fraction,
    config: CostConfig,
    policy_name: str = "default"
) -> Fraction:
    """
    Compute verification_cost(f) = base_fee + λ * Δ⁺ + penalties.
    
    This is the deterministic cost extraction for a transition.
    Under Regime B, this is the canonical spent amount.
    
    Args:
        delta_plus: Δ⁺ = max(0, C(x') - C(x)) - excess violation
        config: Cost configuration
        policy_name: Name of policy for penalty lookup
        
    Returns:
        Total authority spent for this transition
        
    Raises:
        ValueError: If delta_plus exceeds policy bound
        
    Example:
        >>> config = CostConfig(base_fee=Fraction(0), lambda_global=Fraction(1))
        >>> cost = verification_cost(Fraction(5), config)
        >>> print(f"Cost: {cost}")
    """
    # Validate boundedness
    if config.delta_max is not None and delta_plus > config.delta_max:
        raise ValueError(
            f"Violation increase {delta_plus} exceeds policy bound {config.delta_max}"
        )
    
    # Compute cost: base_fee + λ * Δ⁺
    cost = config.base_fee + config.lambda_global * delta_plus
    
    # Add policy penalty if applicable
    penalty = config.get_penalty(policy_name)
    cost += penalty
    
    return cost


def verification_cost_from_scalars(
    scalar_before: Any,
    scalar_after: Any,
    config: CostConfig,
    policy_name: str = "default",
    get_total: Callable[[Any], Fraction] = lambda s: s.total
) -> Fraction:
    """
    Compute verification_cost from pre/post state scalars.
    
    Convenience function that extracts Δ⁺ from CK0Scalar objects.
    
    Args:
        scalar_before: Coherence scalar of pre-state
        scalar_after: Coherence scalar of post-state
        config: Cost configuration
        policy_name: Name of policy for penalty lookup
        get_total: Function to extract total from scalar object
        
    Returns:
        Total authority spent for this transition
    """
    total_before = get_total(scalar_before)
    total_after = get_total(scalar_after)
    
    delta_plus = Fraction(max(0, total_after - total_before))
    
    return verification_cost(delta_plus, config, policy_name)


def receipt_cost(receipt: Any, cost_field: str = "spent_budget") -> Fraction:
    """
    Extract spent budget from a receipt.
    
    This is the canonical value stored in the receipt that
    represents what was actually paid for the transition.
    
    Args:
        receipt: Receipt object
        cost_field: Name of the field containing spent budget
        
    Returns:
        The spent budget as Fraction
        
    Note:
        This assumes the receipt has a numeric 'spent_budget' attribute.
        The actual implementation depends on receipt structure.
    """
    # Try to get the attribute
    if hasattr(receipt, cost_field):
        value = getattr(receipt, cost_field)
        if isinstance(value, Fraction):
            return value
        elif isinstance(value, Number):
            return Fraction(value)
        else:
            raise TypeError(f"Invalid type for {cost_field}: {type(value)}")
    
    # Try as dict-like access
    if isinstance(receipt, dict):
        value = receipt.get(cost_field, Fraction(0))
        if isinstance(value, Number):
            return Fraction(value)
        return value
    
    raise AttributeError(f"Receipt has no field '{cost_field}'")


def compositional_cost_bound(
    cost_f: Fraction,
    cost_g: Fraction
) -> Fraction:
    """
    Compute upper bound on composed cost: |g ∘ f| ≤ |f| + |g|.
    
    This is the subadditivity property that makes the oplax
    structure well-defined. Under Regime B with global λ,
    this always holds.
    
    Args:
        cost_f: Cost of morphism f
        cost_g: Cost of morphism g
        
    Returns:
        Upper bound on composed cost
        
    Example:
        >>> bound = compositional_cost_bound(Fraction(5), Fraction(3))
        >>> assert composed_cost <= bound
    """
    return cost_f + cost_g


def assert_subadditivity(
    cost_f: Fraction,
    cost_g: Fraction,
    cost_composed: Fraction
) -> bool:
    """
    Assert that |g ∘ f| ≤ |f| + |g|.
    
    Used in tests to verify compositionality guarantees.
    
    Args:
        cost_f: Cost of morphism f
        cost_g: Cost of morphism g  
        cost_composed: Cost of composed morphism g ∘ f
        
    Returns:
        True if subadditivity holds
        
    Raises:
        AssertionError: If subadditivity is violated
    """
    bound = compositional_cost_bound(cost_f, cost_g)
    assert cost_composed <= bound, (
        f"Subadditivity violated: |g∘f|={cost_composed} > |f|+|g|={bound}"
    )
    return True


def monotonicity_check(
    cost_before: Fraction,
    cost_after: Fraction
) -> bool:
    """
    Verify monotonicity: cost should not decrease with state progression.
    
    Under Regime B, this is a sanity check - costs are non-negative
    but not necessarily monotonic (they depend on Δ⁺).
    
    Args:
        cost_before: Cost before transition
        cost_after: Cost after transition
        
    Returns:
        True if non-negative (allow any value as long as valid)
    """
    return cost_after >= 0 and cost_before >= 0


# =============================================================================
# Budget Law Integration
# =============================================================================

def budget_decrement(
    current_budget: Fraction,
    spent: Fraction
) -> Fraction:
    """
    Apply budget decrement: b_next = b_prev - spent.
    
    Args:
        current_budget: Current budget
        spent: Amount spent (from verification_cost)
        
    Returns:
        Remaining budget
        
    Raises:
        ValueError: If spent exceeds current_budget
    """
    if spent > current_budget:
        raise ValueError(
            f"Insufficient budget: have {current_budget}, need {spent}"
        )
    return current_budget - spent


def budget_after_transition(
    budget_before: Fraction,
    delta_plus: Fraction,
    config: CostConfig,
    policy_name: str = "default"
) -> Fraction:
    """
    Compute budget after a transition.
    
    Combines verification_cost and budget_decrement.
    
    Args:
        budget_before: Budget before transition
        delta_plus: Δ⁺ for the transition
        config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        Budget after transition
        
    Example:
        >>> config = CostConfig(base_fee=Fraction(0), lambda_global=Fraction(1))
        >>> budget_after = budget_after_transition(Fraction(100), Fraction(5), config)
        >>> assert budget_after == Fraction(95)
    """
    spent = verification_cost(delta_plus, config, policy_name)
    return budget_decrement(budget_before, spent)


# =============================================================================
# Common Configurations
# =============================================================================

# Strict PoC: No violation allowed
STRICT_POC_CONFIG = CostConfig(
    base_fee=Fraction(0),
    lambda_global=Fraction(10**6),  # Very high λ makes any Δ⁺ expensive
    delta_max=Fraction(0)  # Zero tolerance
)

# Lenient PoC: Allow bounded violation
LENIENT_POC_CONFIG = CostConfig(
    base_fee=Fraction(0),
    lambda_global=Fraction(1),
    delta_max=Fraction(10**15)  # Allow up to some threshold
)

# Zero-cost coherent steps only
COHERENT_ONLY_CONFIG = CostConfig(
    base_fee=Fraction(0),
    lambda_global=Fraction(0),
    delta_max=Fraction(0)  # Only allow zero Δ⁺
)

# Production config with penalties
PRODUCTION_CONFIG = CostConfig(
    base_fee=Fraction(10**12),  # Base verification cost
    lambda_global=Fraction(1),
    delta_max=None,  # No hard cap
    penalties=(
        ("unknown_policy", Fraction(10**15)),
        ("unsafe_op", Fraction(10**16)),
        ("unauthorized", Fraction(10**17)),
    )
)
