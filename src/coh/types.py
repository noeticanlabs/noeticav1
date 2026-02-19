"""
Coh Category Types

This module defines the core types for the Category of Coherent Spaces:
- CohObject: a 5-tuple (X, Rec, V, Δ, RV)
- CohMorphism: a pair (f_X, f_♯)

These support both finite and infinite/continuous state spaces via abstract carriers.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Generic, TypeVar, Protocol, Optional
from abc import abstractmethod

# Type variables
X = TypeVar('X')  # State space
R = TypeVar('R')  # Receipt set


class StateCarrier(Protocol):
    """Abstract state carrier supporting both finite and infinite spaces.
    
    Implement this protocol for custom state spaces that may be:
    - Finite sets
    - Continuous manifolds
    - Infinite countable sets
    - Custom geometric spaces
    """
    
    def is_state(self, x: Any) -> bool:
        """Check if x is a valid state"""
        ...
    
    def is_admissible(self, x: Any, eps0: float = 0.0) -> bool:
        """Check if x is admissible (V(x) <= eps0)"""
        ...


class ReceiptCarrier(Protocol):
    """Abstract receipt carrier for algebraic witnesses.
    
    Receipts represent computational, analytic, or cryptographic
    proofs of validity for transitions.
    """
    
    def is_receipt(self, rho: Any) -> bool:
        """Check if rho is a valid receipt"""
        ...


# For finite models, provide simple implementations
class FiniteStateCarrier:
    """Finite state carrier using explicit set"""
    
    def __init__(self, states: set):
        self._states = states
    
    def is_state(self, x: Any) -> bool:
        return x in self._states
    
    def is_admissible(self, x: Any, eps0: float = 0.0) -> bool:
        # This requires a potential function - see CohObject
        raise NotImplementedError("Use CohObject.is_admissible for potential")


class FiniteReceiptCarrier:
    """Finite receipt carrier using explicit set"""
    
    def __init__(self, receipts: set):
        self._receipts = receipts
    
    def is_receipt(self, rho: Any) -> bool:
        return rho in self._receipts


@dataclass(frozen=True)
class CohObject:
    """§1: An object is a 5-tuple (X, Rec, V, Δ, RV)
    
    Uses abstract carriers instead of concrete sets to support
    infinite/continuous state spaces (manifolds, etc.)
    
    Attributes:
        is_state: Predicate for state membership in X
        is_receipt: Predicate for receipt membership in Rec
        potential: V: X → ℝ≥0 (violation functional)
        budget_map: Δ: Rec → ℝ≥0 (budget allowance)
        validate: RV(x, y, ρ) → bool (deterministic validator)
    """
    
    is_state: Callable[[Any], bool]
    is_receipt: Callable[[Any], bool]
    potential: Callable[[Any], float]
    budget_map: Callable[[Any], float]
    validate: Callable[[Any, Any, Any], bool]
    
    def is_admissible(self, x: Any, eps0: float = 0.0) -> bool:
        """§1.4: C = V^{-1}([0, ε₀]) with tolerance for numeric stability
        
        Args:
            x: State to check
            eps0: Tolerance (default 0.0 for exact admissibility)
            
        Returns:
            True if x is admissible (potential <= eps0)
        """
        return self.is_state(x) and self.potential(x) <= eps0
    
    def valid_triples(self) -> list:
        """Iterate valid (x, y, ρ) triples - only for finite models
        
        Raises:
            NotImplementedError: If called on infinite state space
        """
        raise NotImplementedError(
            "valid_triples() only available for finite models. "
            "Use the validate() function directly for infinite spaces."
        )
    
    def transition_relation(self) -> set:
        """§3.1: T = {(x,y) | ∃ρ: RV(x,y,ρ)}
        
        Only available for finite models.
        
        Raises:
            NotImplementedError: If called on infinite state space
        """
        raise NotImplementedError(
            "transition_relation() only available for finite models."
        )


@dataclass(frozen=True)
class CohMorphism(Generic[X, R]):
    """§4: A morphism is a pair (f_X, f_♯)
    
    Morphisms map between CohObjects while preserving the 
    algebraic-geometric binding (A2) and admissibility (M1).
    
    Attributes:
        state_map: f_X: X₁ → X₂ (maps states)
        receipt_map: f_♯: Rec₁ → Rec₂ (maps receipts)
    """
    
    state_map: Callable[[Any], Any]
    receipt_map: Callable[[Any], Any]


# Helper for creating finite model objects
def create_finite_coh_object(
    states: set,
    receipts: set,
    potential: Callable[[Any], float],
    budget_map: Callable[[Any], float],
    valid_transitions: set  # set of (x, y, rho) tuples
) -> CohObject:
    """Create a CohObject from finite sets.
    
    Args:
        states: Set of states X
        receipts: Set of receipts Rec
        potential: V: X → ℝ≥0
        budget_map: Δ: Rec → ℝ≥0
        valid_transitions: Set of (x, y, rho) tuples where RV(x,y,rho) is True
        
    Returns:
        CohObject with finite carrier
    """
    
    def is_state(x: Any) -> bool:
        return x in states
    
    def is_receipt(rho: Any) -> bool:
        return rho in receipts
    
    # Build validator from transition set
    transition_set = valid_transitions
    
    def validate(x: Any, y: Any, rho: Any) -> bool:
        return (x, y, rho) in transition_set
    
    # Create object
    obj = CohObject(
        is_state=is_state,
        is_receipt=is_receipt,
        potential=potential,
        budget_map=budget_map,
        validate=validate
    )
    
    # Add finite model helper using object.__setattr__ (bypasses frozen)
    def valid_triples():
        return list(transition_set)
    
    def transition_relation():
        return {(x, y) for x, y, rho in transition_set}
    
    object.__setattr__(obj, 'valid_triples', valid_triples)
    object.__setattr__(obj, 'transition_relation', transition_relation)
    
    return obj


__all__ = [
    'CohObject',
    'CohMorphism',
    'StateCarrier',
    'ReceiptCarrier',
    'FiniteStateCarrier',
    'FiniteReceiptCarrier',
    'create_finite_coh_object',
]
