"""
Coh Category Structure

This module implements the category structure: identity, composition,
and verification of category laws.
"""

from typing import Any

from .types import CohObject, CohMorphism
from . import morphisms


def identity(obj: CohObject) -> CohMorphism:
    """§6.1: id_S = (id_X, id_Rec)
    
    The identity morphism for a CohObject.
    
    Args:
        obj: CohObject to create identity for
        
    Returns:
        Identity morphism (id_X, id_Rec)
    """
    return CohMorphism(
        state_map=lambda x: x,
        receipt_map=lambda rho: rho
    )


def compose(f: CohMorphism, g: CohMorphism) -> CohMorphism:
    """§6.2: g ∘ f = (g_X ∘ f_X, g_♯ ∘ f_♯)
    
    Composition of morphisms.
    
    Args:
        f: First morphism (domain → codomain)
        g: Second morphism (domain → codomain)
        
    Returns:
        Composed morphism g ∘ f
        
    Note:
        Does NOT verify M1/M2. Use compose_checked for verification.
    """
    return CohMorphism(
        state_map=lambda x: g.state_map(f.state_map(x)),
        receipt_map=lambda rho: g.receipt_map(f.receipt_map(rho))
    )


def compose_checked(
    f: CohMorphism,
    g: CohMorphism,
    dom: CohObject,
    mid: CohObject,
    cod: CohObject
) -> CohMorphism:
    """Compose with axiom verification.
    
    Composes f: dom → mid and g: mid → cod, verifying M1 and M2.
    
    Args:
        f: First morphism (dom → mid)
        g: Second morphism (mid → cod)
        dom: Domain object
        mid: Middle (codomain of f, domain of g)
        cod: Codomain object
        
    Returns:
        Composed morphism g ∘ f
        
    Raises:
        AssertionError: If M1 or M2 fails
    """
    result = compose(f, g)
    
    # Verify M1: admissibility preservation
    assert morphisms.verify_admissibility_preservation(result, dom, cod), \
        "M1 failed: admissibility not preserved"
    
    # Verify M2: receipt covariance
    assert morphisms.verify_receipt_covariance(result, dom, cod), \
        "M2 failed: receipt covariance failed"
    
    return result


# Category law verification

def verify_identity_left(
    f: CohMorphism,
    dom: CohObject,
    cod: CohObject
) -> bool:
    """Verify: id ∘ f = f
    
    Args:
        f: Morphism
        dom: Domain of f
        cod: Codomain of f
        
    Returns:
        True if law holds
    """
    id_dom = identity(dom)
    composed = compose(id_dom, f)
    return composed == f


def verify_identity_right(
    f: CohMorphism,
    dom: CohObject,
    cod: CohObject
) -> bool:
    """Verify: f ∘ id = f
    
    Args:
        f: Morphism
        dom: Domain of f
        cod: Codomain of f
        
    Returns:
        True if law holds
    """
    id_cod = identity(cod)
    composed = compose(f, id_cod)
    return composed == f


def verify_associativity(
    f: CohMorphism,
    g: CohMorphism,
    h: CohMorphism,
    dom: CohObject,
    mid1: CohObject,
    mid2: CohObject,
    cod: CohObject
) -> bool:
    """Verify: (h ∘ g) ∘ f = h ∘ (g ∘ f)
    
    Args:
        f: First morphism (dom → mid1)
        g: Second morphism (mid1 → mid2)
        h: Third morphism (mid2 → cod)
        dom: Domain
        mid1: First middle
        mid2: Second middle
        cod: Codomain
        
    Returns:
        True if law holds
    """
    left = compose(compose(f, g), h)
    right = compose(f, compose(g, h))
    return left == right


class CohCategory:
    """The Coh category.
    
    Provides methods for identity, composition, and law verification.
    """
    
    @staticmethod
    def id(obj: CohObject) -> CohMorphism:
        """Identity morphism"""
        return identity(obj)
    
    @staticmethod
    def compose(f: CohMorphism, g: CohMorphism) -> CohMorphism:
        """Composition"""
        return compose(f, g)
    
    @staticmethod
    def compose_checked(
        f: CohMorphism,
        g: CohMorphism,
        dom: CohObject,
        mid: CohObject,
        cod: CohObject
    ) -> CohMorphism:
        """Composition with verification"""
        return compose_checked(f, g, dom, mid, cod)
    
    @staticmethod
    def verify_laws(
        f: CohMorphism,
        g: CohMorphism,
        h: CohMorphism,
        dom: CohObject,
        mid1: CohObject,
        mid2: CohObject,
        cod: CohObject
    ) -> dict:
        """Verify all category laws.
        
        Returns:
            Dict with law names and results
        """
        return {
            'identity_left': verify_identity_left(f, dom, mid1),
            'identity_right': verify_identity_right(h, mid2, cod),
            'associativity': verify_associativity(f, g, h, dom, mid1, mid2, cod),
        }


__all__ = [
    'identity',
    'compose',
    'compose_checked',
    'verify_identity_left',
    'verify_identity_right',
    'verify_associativity',
    'CohCategory',
]
