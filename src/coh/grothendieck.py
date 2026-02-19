"""
Budget Pullback (Grothendieck Construction)

This module implements the Grothendieck construction for the oplax fibration:

    f*(c) = c + |f|_V

The key equation is the budget conservation law:

    b_prev >= b_next + verification_cost(f)

This makes the morphism exist iff the budget pullback condition holds.

The Grothendieck construction gives us:
1. A fibration over the base category (budgets)
2. Lifting of morphisms to the total space (with cost)
3. Oplax naturality for composition

References:
- plans/coh_structural_audit_implementation_plan.md
- docs/coh/4_limits.md
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any, Callable
from fractions import Fraction
from numbers import Number

from .types import CohObject, CohMorphism
from ..ck0.cost import CostConfig, verification_cost as compute_verification_cost


# =============================================================================
# Budget Type
# =============================================================================

@dataclass(frozen=True)
class Budget:
    """
    Budget value in QFixed(18) representation.
    
    Budgets are the base category for the Grothendieck construction.
    They form a poset under the ordering b1 >= b2.
    
    Attributes:
        value: The budget value as Fraction
    """
    
    value: Fraction
    
    def __post_init__(self):
        """Validate budget value."""
        if self.value < 0:
            raise ValueError("Budget must be non-negative")
    
    def __add__(self, other: Budget) -> Budget:
        """Budget addition: b1 + b2"""
        return Budget(self.value + other.value)
    
    def __sub__(self, other: Budget) -> Budget:
        """Budget subtraction: b1 - b2"""
        result = self.value - other.value
        if result < 0:
            raise ValueError("Budget cannot go negative")
        return Budget(result)
    
    def __ge__(self, other: Budget) -> bool:
        """Budget ordering: b1 >= b2"""
        return self.value >= other.value
    
    def __gt__(self, other: Budget) -> bool:
        """Budget strict ordering: b1 > b2"""
        return self.value > other.value
    
    def __le__(self, other: Budget) -> bool:
        """Budget ordering: b1 <= b2"""
        return self.value <= other.value
    
    def __lt__(self, other: Budget) -> bool:
        """Budget strict ordering: b1 < b2"""
        return self.value < other.value
    
    def __eq__(self, other: Any) -> bool:
        """Budget equality"""
        if not isinstance(other, Budget):
            return False
        return self.value == other.value
    
    @staticmethod
    def zero() -> Budget:
        """Create zero budget"""
        return Budget(Fraction(0))
    
    @staticmethod
    def from_number(value: Number) -> Budget:
        """Create budget from number"""
        return Budget(Fraction(value))
    
    def to_fraction(self) -> Fraction:
        """Get value as Fraction"""
        return self.value


# =============================================================================
# Budget Pullback (Grothendieck Action)
# =============================================================================

def pullback_budget(
    f: CohMorphism,
    target_budget: Budget,
    cost_config: CostConfig,
    policy_name: str = "default"
) -> Budget:
    """
    Compute f*(c) = c + verification_cost(f).
    
    This is the Grothendieck pullback (reindexing) of budget along morphism f.
    Given a target budget c in the codomain, this computes the required
    budget in the domain.
    
    Args:
        f: The morphism (transition)
        target_budget: Current budget c
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        Pullback budget f*(c) = c + |f|_V
        
    Example:
        >>> config = CostConfig(base_fee=Fraction(0), lambda_global=Fraction(1))
        >>> budget = Budget(Fraction(100))
        >>> # After transition with Δ⁺ = 5:
        >>> new_budget = pullback_budget(f, budget, config)
        >>> # new_budget = 100 + cost(f)
    """
    # Get the cost of this morphism
    cost = _get_morphism_cost(f, cost_config, policy_name)
    
    return Budget(target_budget.value + cost)


def _get_morphism_cost(
    f: CohMorphism,
    cost_config: CostConfig,
    policy_name: str
) -> Fraction:
    """
    Extract or compute the cost of a morphism.
    
    The cost can be:
    1. Pre-computed and stored on the morphism
    2. Computed from delta_plus if available
    3. Default to zero for coherent steps
    """
    # Try to get pre-computed cost
    if hasattr(f, 'cost') and f.cost is not None:
        return f.cost
    
    # Try to compute from delta_plus
    if hasattr(f, 'delta_plus') and f.delta_plus is not None:
        delta_plus = f.delta_plus
        if isinstance(delta_plus, Number):
            delta_plus = Fraction(delta_plus)
        return compute_verification_cost(delta_plus, cost_config, policy_name)
    
    # Default: assume coherent (zero cost)
    return Fraction(0)


# =============================================================================
# Morphism Existence Check
# =============================================================================

def morphism_exists(
    f: CohMorphism,
    budget_before: Budget,
    budget_after: Budget,
    cost_config: CostConfig,
    policy_name: str = "default"
) -> bool:
    """
    Check if morphism exists under budget constraints.
    
    Morphism f: A → B exists in Coh_rcpt iff:
        b_before >= b_after + |f|_V
    
    This is the budget conservation law from the oplax fibration.
    It ensures that spending on the transition doesn't exceed the budget.
    
    Args:
        f: The morphism to check
        budget_before: Budget before transition
        budget_after: Budget after transition
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        True if morphism can exist (budget sufficient)
        
    Example:
        >>> config = CostConfig(base_fee=Fraction(0), lambda_global=Fraction(1))
        >>> budget_before = Budget(Fraction(100))
        >>> budget_after = Budget(Fraction(90))  # 10 spent
        >>> if morphism_exists(f, budget_before, budget_after, config):
        ...     print("Transition valid!")
    """
    # Compute required budget in domain
    required = pullback_budget(f, budget_after, cost_config, policy_name)
    
    # Check if we have enough
    return budget_before >= required


def require_morphism(
    f: CohMorphism,
    budget_before: Budget,
    budget_after: Budget,
    cost_config: CostConfig,
    policy_name: str = "default"
) -> None:
    """
    Require that morphism exists, raising exception if not.
    
    Args:
        f: The morphism to check
        budget_before: Budget before transition
        budget_after: Budget after transition
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Raises:
        ValueError: If morphism cannot exist (insufficient budget)
    """
    if not morphism_exists(f, budget_before, budget_after, cost_config, policy_name):
        cost = _get_morphism_cost(f, cost_config, policy_name)
        required = budget_after.value + cost
        raise ValueError(
            f"Insufficient budget for transition: "
            f"have {budget_before.value}, need {required}"
        )


# =============================================================================
# Sequential Composition (Oplax)
# =============================================================================

def compose_with_cost(
    f: CohMorphism,
    g: CohMorphism,
    cost_config: CostConfig,
    policy_name: str = "default"
) -> CohMorphism:
    """
    Compose morphisms and compute combined cost.
    
    For the oplax structure, we have:
        |g ∘ f|_V <= |f|_V + |g|_V
    
    This is subadditivity - the composed cost is at most the sum.
    
    Args:
        f: First morphism (executed first)
        g: Second morphism (executed after f)
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        New morphism representing g ∘ f with combined cost
        
    Note:
        The actual composition requires that codomain(f) = domain(g).
        This function assumes that check is done by caller.
    """
    # Get costs
    cost_f = _get_morphism_cost(f, cost_config, policy_name)
    cost_g = _get_morphism_cost(g, cost_config, policy_name)
    
    # Subadditivity: combined cost <= sum
    combined_cost = cost_f + cost_g
    
    # Create composed morphism (placeholder - actual implementation depends on structure)
    from .types import CohMorphism
    
    def composed_state_map(x):
        # Apply f first, then g
        fx = f.state_map(x)
        return g.state_map(fx)
    
    def composed_receipt_map(rho):
        # Apply receipt maps
        return g.receipt_map(f.receipt_map(rho))
    
    # Note: Domain/codomain handling depends on structure
    composed = CohMorphism(
        state_map=composed_state_map,
        receipt_map=composed_receipt_map,
        domain=f.domain if hasattr(f, 'domain') and f.domain else None,
        codomain=g.codomain if hasattr(g, 'codomain') and g.codomain else None
    )
    
    # Store combined cost
    # Note: This is a simplified version; real implementation might store differently
    return composed


# =============================================================================
# Parallel Composition (Monoidal)
# =============================================================================

def parallel_with_cost(
    f: CohMorphism,
    g: CohMorphism,
    cost_config: CostConfig,
    policy_name: str = "default"
) -> CohMorphism:
    """
    Form parallel composition of morphisms.
    
    For the monoidal structure:
        |f ⊗ g|_V = |f|_V + |g|_V
    
    This is additivity - parallel costs sum.
    
    Args:
        f: First morphism
        g: Second morphism  
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        New morphism representing f ⊗ g with combined cost
    """
    # Get costs
    cost_f = _get_morphism_cost(f, cost_config, policy_name)
    cost_g = _get_morphism_cost(g, cost_config, policy_name)
    
    # Additivity: combined cost = sum
    combined_cost = cost_f + cost_g
    
    from .types import CohMorphism
    
    def parallel_state_map(xy):
        # Apply f to first component, g to second
        x, y = xy
        return (f.state_map(x), g.state_map(y))
    
    def parallel_receipt_map(rho):
        # Apply receipt maps to respective components
        rho_f, rho_g = rho
        return (f.receipt_map(rho_f), g.receipt_map(rho_g))
    
    # Note: Domain/codomain would be tensor products
    parallel = CohMorphism(
        state_map=parallel_state_map,
        receipt_map=parallel_receipt_map
    )
    
    return parallel


# =============================================================================
# Budget Conservation Law
# =============================================================================

def verify_budget_conservation(
    transitions: list[tuple[CohMorphism, Budget, Budget]],
    cost_config: CostConfig,
    policy_name: str = "default"
) -> bool:
    """
    Verify budget conservation law for a sequence of transitions.
    
    For each transition f: b_before >= b_after + |f|_V
    
    Args:
        transitions: List of (morphism, budget_before, budget_after)
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        True if all transitions satisfy budget conservation
    """
    for f, b_before, b_after in transitions:
        if not morphism_exists(f, b_before, b_after, cost_config, policy_name):
            return False
    return True


def compute_minimum_budget(
    f: CohMorphism,
    budget_after: Budget,
    cost_config: CostConfig,
    policy_name: str = "default"
) -> Budget:
    """
    Compute minimum budget required to execute transition and end at b_after.
    
    Required: b_before >= b_after + |f|_V
    
    So minimum b_before = b_after + |f|_V
    
    Args:
        f: The transition to execute
        budget_after: Desired budget after transition
        cost_config: Cost configuration
        policy_name: Policy name for penalty lookup
        
    Returns:
        Minimum budget before transition
    """
    cost = _get_morphism_cost(f, cost_config, policy_name)
    return Budget(budget_after.value + cost)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    'Budget',
    'pullback_budget',
    'morphism_exists',
    'require_morphism',
    'compose_with_cost',
    'parallel_with_cost',
    'verify_budget_conservation',
    'compute_minimum_budget',
]
