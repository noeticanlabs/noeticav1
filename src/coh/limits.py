"""
Coh Limits

This module implements categorical limits: products and pullbacks.
"""

from typing import Any, Tuple, List, Set, Callable

from .types import CohObject, CohMorphism, create_finite_coh_object


def product(obj1: CohObject, obj2: CohObject) -> CohObject:
    """§7.1: Product of two Coh objects
    
    Given objects S₁ = (X₁, Rec₁, V₁, Δ₁, RV₁) and S₂:
    
    - X_× = X₁ × X₂
    - V_×(x₁, x₂) = V₁(x₁) + V₂(x₂)
    - C_× = C₁ × C₂
    - Rec_× = Rec₁ × Rec₂
    - Δ_×(ρ₁, ρ₂) = Δ₁(ρ₁) + Δ₂(ρ₂)
    - RV_×((x₁,x₂),(y₁,y₂),(ρ₁,ρ₂)) ⟺ RV₁(x₁,y₁,ρ₁) ∧ RV₂(x₂,y₂,ρ₂)
    
    Args:
        obj1: First CohObject
        obj2: Second CohObject
        
    Returns:
        Product object S₁ × S₂
        
    Note:
        Only works for finite models.
    """
    # Get finite model helpers
    triples1 = obj1.valid_triples()
    triples2 = obj2.valid_triples()
    
    # Build state and receipt spaces
    states1 = {x for x, y, rho in triples1}
    states2 = {x for x, y, rho in triples2}
    receipts1 = {rho for x, y, rho in triples1}
    receipts2 = {rho for x, y, rho in triples2}
    
    X_product = {(x1, x2) for x1 in states1 for x2 in states2}
    Rec_product = {(r1, r2) for r1 in receipts1 for r2 in receipts2}
    
    # Potential is sum
    def V_product(pair):
        x1, x2 = pair
        return obj1.potential(x1) + obj2.potential(x2)
    
    # Budget is sum
    def Delta_product(pair):
        r1, r2 = pair
        return obj1.budget_map(r1) + obj2.budget_map(r2)
    
    # Validator: RV_×((x1,x2),(y1,y2),(ρ1,ρ2)) ⟺ RV₁∧RV₂
    # Build all valid triples for product
    valid_transitions = set()
    for x1, y1, rho1 in triples1:
        for x2, y2, rho2 in triples2:
            # Check both validators
            if obj1.validate(x1, y1, rho1) and obj2.validate(x2, y2, rho2):
                valid_transitions.add(
                    ((x1, x2), (y1, y2), (rho1, rho2))
                )
    
    return create_finite_coh_object(
        states=X_product,
        receipts=Rec_product,
        potential=V_product,
        budget_map=Delta_product,
        valid_transitions=valid_transitions
    )


def product_projections(obj1: CohObject, obj2: CohObject) -> Tuple[CohMorphism, CohMorphism]:
    """Get projection morphisms for product.
    
    Args:
        obj1: First object
        obj2: Second object
        
    Returns:
        Tuple (π₁, π₂) of projection morphisms
    """
    prod = product(obj1, obj2)
    
    # π₁: S₁ × S₂ → S₁
    pi1 = CohMorphism(
        state_map=lambda pair: pair[0],
        receipt_map=lambda pair: pair[0]
    )
    
    # π₂: S₁ × S₂ → S₂
    pi2 = CohMorphism(
        state_map=lambda pair: pair[1],
        receipt_map=lambda pair: pair[1]
    )
    
    return pi1, pi2


def pullback(
    A: CohObject,
    B: CohObject,
    p: CohMorphism,  # A → O
    l: CohMorphism   # B → O
) -> CohObject:
    """§7.2: Pullback (fiber product) of A and B over O
    
    Given morphisms:
    - p: A → O
    - l: B → O
    
    The pullback X_pb = {(a, b) | p_X(a) = l_X(b)}
    
    - X_pb = subspace of X_A × X_B where projections agree
    - Rec_pb = {(ρ_A, ρ_B) | p_♯(ρ_A) = l_♯(ρ_B)}
    - V_pb(a, b) = V_A(a) + V_B(b)
    - Δ_pb(ρ_A, ρ_B) = Δ_A(ρ_A) + Δ_B(ρ_B)
    - RV_pb((a₁,b₁),(a₂,b₂),(ρ_A,ρ_B)) ⟺ RV_A ∧ RV_B ∧ p_♯(ρ_A)=l_♯(ρ_B)
    
    Args:
        A: Object A
        B: Object B  
        p: Morphism A → O
        l: Morphism B → O
        
    Returns:
        Pullback object A ×_O B
        
    Note:
        Only works for finite models.
    """
    # Get finite model helpers
    triples_A = A.valid_triples()
    triples_B = B.valid_triples()
    
    states_A = {x for x, y, rho in triples_A}
    states_B = {x for x, y, rho in triples_B}
    receipts_A = {rho for x, y, rho in triples_A}
    receipts_B = {rho for x, y, rho in triples_B}
    
    # X_pb = {(a,b) | p_X(a) = l_X(b)}
    X_pb = [
        (a, b)
        for a in states_A
        for b in states_B
        if p.state_map(a) == l.state_map(b)
    ]
    
    # Rec_pb = {(ρ_A, ρ_B) | p_♯(ρ_A) = l_♯(ρ_B)}
    Rec_pb = [
        (rho_a, rho_b)
        for rho_a in receipts_A
        for rho_b in receipts_B
        if p.receipt_map(rho_a) == l.receipt_map(rho_b)
    ]
    
    # Potential is sum
    def V_pb(pair):
        a, b = pair
        return A.potential(a) + B.potential(b)
    
    # Budget is sum
    def Delta_pb(pair):
        rho_a, rho_b = pair
        return A.budget_map(rho_a) + B.budget_map(rho_b)
    
    # Validator: both RV_A and RV_B must hold, plus receipt compatibility
    valid_transitions = set()
    for a1, a2, rho_a in triples_A:
        for b1, b2, rho_b in triples_B:
            # Check RV_A
            if not A.validate(a1, a2, rho_a):
                continue
            # Check RV_B  
            if not B.validate(b1, b2, rho_b):
                continue
            # Check receipt compatibility
            if p.receipt_map(rho_a) != l.receipt_map(rho_b):
                continue
            # Valid pullback transition
            valid_transitions.add(
                ((a1, b1), (a2, b2), (rho_a, rho_b))
            )
    
    return create_finite_coh_object(
        states=set(X_pb),
        receipts=set(Rec_pb),
        potential=V_pb,
        budget_map=Delta_pb,
        valid_transitions=valid_transitions
    )


def pullback_projections(
    A: CohObject,
    B: CohObject,
    p: CohMorphism,
    l: CohMorphism
) -> Tuple[CohMorphism, CohMorphism]:
    """Get projection morphisms for pullback.
    
    Args:
        A: Object A
        B: Object B
        p: Morphism A → O
        l: Morphism B → O
        
    Returns:
        Tuple (π_A, π_B) of projection morphisms
    """
    pb = pullback(A, B, p, l)
    
    # π_A: pb → A
    pi_a = CohMorphism(
        state_map=lambda pair: pair[0],  # (a, b) -> a
        receipt_map=lambda pair: pair[0]  # (rho_a, rho_b) -> rho_a
    )
    
    # π_B: pb → B
    pi_b = CohMorphism(
        state_map=lambda pair: pair[1],  # (a, b) -> b
        receipt_map=lambda pair: pair[1]  # (rho_a, rho_b) -> rho_b
    )
    
    return pi_a, pi_b


__all__ = [
    'product',
    'product_projections',
    'pullback',
    'pullback_projections',
]
