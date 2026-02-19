"""
Coh CK-0 Integration

This module defines Coh_CK0 - the full subcategory of Coh
where objects satisfy CK-0 canonical form.

CK-0 objects have:
- V(x) = r̃(x)ᵀ W r̃(x) (weighted residual norm)
- Receipts with CK-0 schema (policy_id, budget, debt, hash)
- Validator enforcing CK-0 descent theorem
"""

from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

from .types import CohObject, CohMorphism
from . import objects as coh_objects
from . import morphisms as coh_morphisms


# CK-0 receipt schema
CK0_RECEIPT_FIELDS = {
    'policy_id',    # Policy identifier
    'budget',       # Declared service budget
    'debt',         # Current debt
    'residual',     # Residual values r̃(x)
    'hash',         # Cryptographic digest
    'timestamp',    # Service time
}


def is_ck0_receipt(receipt: Any) -> bool:
    """Check if a receipt has CK-0 schema.
    
    Args:
        receipt: Receipt to check
        
    Returns:
        True if receipt has all required CK-0 fields
    """
    if not isinstance(receipt, dict):
        return False
    return all(field in receipt for field in CK0_RECEIPT_FIELDS)


def create_ck0_potential(
    residual_fn: Callable[[Any], list],
    weight_matrix: list
) -> Callable[[Any], float]:
    """Create CK-0 potential from residual function and weight matrix.
    
    V(x) = r̃(x)ᵀ W r̃(x)
    
    Args:
        residual_fn: Function computing residual r̃(x)
        weight_matrix: SPD weight matrix W
        
    Returns:
        Potential function V: X → ℝ≥0
    """
    def V(x):
        r = residual_fn(x)
        # rᵀ W r = sum_i,j r_i * W_ij * r_j
        result = 0.0
        for i, ri in enumerate(r):
            for j, rj in enumerate(r):
                result += ri * weight_matrix[i][j] * rj
        return result
    return V


def create_ck0_validator(
    potential_fn: Callable[[Any], float]
) -> Callable[[Any, Any, Any], bool]:
    """Create CK-0 validator enforcing descent theorem.
    
    RV(x, y, ρ) ⟺ V(y) ≤ V(x) - δ(ρ) + Δ(ρ)
    
    where δ(ρ) = debt, Δ(ρ) = budget
    
    Args:
        potential_fn: Potential function V
        
    Returns:
        Validator function (x, y, rho) -> bool
    """
    def validate(x: Any, y: Any, rho: Any) -> bool:
        # Must be CK-0 receipt
        if not is_ck0_receipt(rho):
            return False
        
        Vx = potential_fn(x)
        Vy = potential_fn(y)
        
        # Descent: Vy ≤ Vx - debt + budget
        debt = rho.get('debt', 0)
        budget = rho.get('budget', 0)
        
        return Vy <= Vx - debt + budget
    
    return validate


class CohCK0Object(CohObject):
    """Coh object with CK-0 canonical form.
    
    Inherits from CohObject but enforces CK-0 structure:
    - Potential is weighted residual norm
    - Receipts have CK-0 schema
    - Validator enforces descent theorem
    """
    
    def __init__(
        self,
        is_state: Callable[[Any], bool],
        is_receipt: Callable[[Any], bool],
        potential: Callable[[Any], float],
        budget_map: Callable[[Any], float],
        validate: Callable[[Any, Any, Any], bool],
        weight_matrix: Optional[list] = None,
        residual_fn: Optional[Callable[[Any], list]] = None
    ):
        super().__init__(
            is_state=is_state,
            is_receipt=is_receipt,
            potential=potential,
            budget_map=budget_map,
            validate=validate
        )
        self.weight_matrix = weight_matrix
        self.residual_fn = residual_fn
    
    @staticmethod
    def is_ck0(obj: CohObject) -> bool:
        """Check if CohObject satisfies CK-0 canonical form.
        
        Args:
            obj: CohObject to check
            
        Returns:
            True if object is CK-0 compatible
        """
        # Check that receipts have CK-0 schema
        try:
            for x, y, rho in obj.valid_triples():
                if not is_ck0_receipt(rho):
                    return False
            return True
        except NotImplementedError:
            # Can't verify for infinite models
            return False
    
    @staticmethod
    def from_residual(
        is_state: Callable[[Any], bool],
        is_receipt: Callable[[Any], bool],
        residual_fn: Callable[[Any], list],
        weight_matrix: list,
        valid_transitions: list,
        get_budget: Callable[[Any], float] = lambda rho: rho.get('budget', 0)
    ) -> 'CohCK0Object':
        """Create CK-0 object from residual function.
        
        Convenience constructor for CK-0 objects.
        
        Args:
            is_state: State predicate
            is_receipt: Receipt predicate
            residual_fn: r̃(x) computation
            weight_matrix: SPD weight matrix W
            valid_transitions: List of (x, y, rho) tuples
            get_budget: Function to extract budget from receipt
            
        Returns:
            CohCK0Object
        """
        potential = create_ck0_potential(residual_fn, weight_matrix)
        validate = create_ck0_potential(potential)
        
        # Wrap to include debt check
        def ck0_validate(x, y, rho):
            if not is_ck0_receipt(rho):
                return False
            Vx = potential(x)
            Vy = potential(y)
            debt = rho.get('debt', 0)
            budget = rho.get('budget', 0)
            return Vy <= Vx - debt + budget
        
        def budget_map(rho):
            return rho.get('budget', 0) if is_ck0_receipt(rho) else 0
        
        return CohCK0Object(
            is_state=is_state,
            is_receipt=is_receipt,
            potential=potential,
            budget_map=budget_map,
            validate=ck0_validate,
            weight_matrix=weight_matrix,
            residual_fn=residual_fn
        )


class CohCK0Morphism(CohMorphism):
    """Morphism in Coh_CK0.
    
    A morphism between CK-0 objects that preserves CK-0 structure.
    """
    
    def __init__(
        self,
        state_map: Callable[[Any], Any],
        receipt_map: Callable[[Any], Any],
        preserves_ck0: bool = True
    ):
        super().__init__(
            state_map=state_map,
            receipt_map=receipt_map
        )
        self.preserves_ck0 = preserves_ck0


class CohCK0Category:
    """Full subcategory of Coh on CK-0 objects.
    
    Provides methods for working with CK-0 compatible objects.
    """
    
    @staticmethod
    def is_object(obj: CohObject) -> bool:
        """Check if object is in Coh_CK0"""
        return CohCK0Object.is_ck0(obj)
    
    @staticmethod
    def is_morphism(
        f: CohMorphism,
        dom: CohObject,
        cod: CohObject
    ) -> bool:
        """Check if morphism is in Coh_CK0"""
        # Domain and codomain must be CK-0
        if not CohCK0Object.is_ck0(dom):
            return False
        if not CohCK0Object.is_ck0(cod):
            return False
        
        # Verify M1 and M2
        if not coh_morphisms.verify_admissibility_preservation(f, dom, cod):
            return False
        if not coh_morphisms.verify_receipt_covariance(f, dom, cod):
            return False
        
        return True


# Inclusion functor from Coh_CK0 to Coh
class InclusionFunctor:
    """Inclusion functor I: Coh_CK0 → Coh"""
    
    @staticmethod
    def map_object(obj: CohObject) -> CohObject:
        """Identity on objects"""
        return obj
    
    @staticmethod
    def map_morphism(f: CohMorphism) -> CohMorphism:
        """Identity on morphisms"""
        return f


# Violation functor restricted to CK-0
class CK0ViolationFunctor:
    """Vio|_CK0: Coh_CK0 → Set^ℝ≥0"""
    
    @staticmethod
    def map(obj: CohCK0Object):
        """Map CK-0 object to its potential"""
        return obj.potential


__all__ = [
    'CohCK0Object',
    'CohCK0Morphism', 
    'CohCK0Category',
    'InclusionFunctor',
    'CK0ViolationFunctor',
    'is_ck0_receipt',
    'CK0_RECEIPT_FIELDS',
    'create_ck0_potential',
    'create_ck0_validator',
]
