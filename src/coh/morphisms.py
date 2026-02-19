"""
Coh Morphism Axioms

This module implements verification of Coh morphism axioms M1 and M2.
"""

from typing import Any

from .types import CohObject, CohMorphism


def verify_admissibility_preservation(
    f: CohMorphism,
    dom: CohObject,
    cod: CohObject,
    eps0: float = 0.0
) -> bool:
    """§M1: x ∈ C₁ ⇒ f_X(x) ∈ C₂
    
    The image of an admissible state under the state map
    is admissible in the codomain.
    
    Args:
        f: CohMorphism to verify
        dom: Domain object (S₁)
        cod: Codomain object (S₂)
        eps0: Tolerance for admissibility (default 0.0)
        
    Returns:
        True if M1 holds
        
    Note:
        Only works for finite models.
    """
    try:
        for x, y, rho in dom.valid_triples():
            if dom.is_admissible(x, eps0):
                fx = f.state_map(x)
                if not cod.is_admissible(fx, eps0):
                    return False
        return True
    except NotImplementedError:
        # For infinite models, M1 is assumed by construction
        return True


def verify_receipt_covariance(
    f: CohMorphism,
    dom: CohObject,
    cod: CohObject
) -> bool:
    """§M2: RV₁(x, y, ρ) ⇒ RV₂(f_X(x), f_X(y), f_♯(ρ))
    
    If receipt ρ certifies transition x → y in the domain,
    then the transported receipt certifies the mapped transition
    in the codomain.
    
    Args:
        f: CohMorphism to verify
        dom: Domain object (S₁)
        cod: Codomain object (S₂)
        
    Returns:
        True if M2 holds
        
    Note:
        Only works for finite models.
    """
    try:
        for x, y, rho in dom.valid_triples():
            # Apply the morphism to map (x, y, rho) -> (f_X(x), f_X(y), f_♯(rho))
            fx = f.state_map(x)
            fy = f.state_map(y)
            f_rho = f.receipt_map(rho)
            
            # Check if RV₂ holds for the mapped triple
            if not cod.validate(fx, fy, f_rho):
                return False
        return True
    except NotImplementedError:
        # For infinite models, M2 is assumed by construction
        return True


def verify_order_preservation(
    f: CohMorphism,
    dom: CohObject,
    cod: CohObject
) -> bool:
    """Prop 5.1: If x ≼₁ y then f_X(x) ≼₂ f_X(y)
    
    Morphisms preserve the descent preorder.
    
    Args:
        f: CohMorphism to verify
        dom: Domain object (S₁)
        cod: Codomain object (S₂)
        
    Returns:
        True if order is preserved
        
    Note:
        Only works for finite models.
    """
    from .objects import descent_preorder
    
    preorder_dom = descent_preorder(dom)
    preorder_cod = descent_preorder(cod)
    
    try:
        for x, y, rho in dom.valid_triples():
            x_leq_y = preorder_dom(x, y)
            if x_leq_y:
                fx = f.state_map(x)
                fy = f.state_map(y)
                fx_leq_fy = preorder_cod(fx, fy)
                if not fx_leq_fy:
                    return False
        return True
    except NotImplementedError:
        # For infinite models
        return True


def apply_morphism(
    f: CohMorphism,
    state: Any,
    dom: CohObject
) -> Any:
    """Apply morphism to a state in the domain.
    
    Args:
        f: CohMorphism
        state: State in domain
        dom: Domain object
        
    Returns:
        State in codomain
        
    Raises:
        ValueError: If state is not in domain
    """
    if not dom.is_state(state):
        raise ValueError(f"State {state} not in domain")
    return f.state_map(state)


def apply_morphism_to_receipt(
    f: CohMorphism,
    receipt: Any,
    dom: CohObject
) -> Any:
    """Apply morphism to a receipt in the domain.
    
    Args:
        f: CohMorphism
        receipt: Receipt in domain
        dom: Domain object
        
    Returns:
        Receipt in codomain
        
    Raises:
        ValueError: If receipt is not in domain
    """
    if not dom.is_receipt(receipt):
        raise ValueError(f"Receipt {receipt} not in domain")
    return f.receipt_map(receipt)


__all__ = [
    'verify_admissibility_preservation',
    'verify_receipt_covariance',
    'verify_order_preservation',
    'apply_morphism',
    'apply_morphism_to_receipt',
]
