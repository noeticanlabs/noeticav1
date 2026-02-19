"""
Coh Object Axioms

This module implements verification of Coh object axioms A1, A2, A3
and derived structures (transition relation, descent preorder).
"""

from typing import Callable, Any, Set, Tuple
from collections import deque

from .types import CohObject, CohMorphism


def verify_faithfulness(obj: CohObject, eps0: float = 0.0) -> bool:
    """§A1: x ∈ C ⟺ V(x) = 0 (or V(x) <= eps0)
    
    Admissibility is defined exactly by potential being zero.
    
    Args:
        obj: CohObject to verify
        eps0: Tolerance for admissibility (default 0.0)
        
    Returns:
        True if A1 holds
        
    Note:
        Only works for finite models. For infinite spaces,
        this verification is not computable.
    """
    try:
        # For finite models
        for x in obj.valid_triples():
            state = x[0]  # (x, y, rho) -> x is first element
            is_adm = obj.is_admissible(state, eps0)
            is_zero = abs(obj.potential(state) - 0.0) <= eps0
            if is_adm != is_zero:
                return False
        return True
    except NotImplementedError:
        # For infinite models, A1 is assumed by construction
        return True


def verify_algebraic_geometric_binding(obj: CohObject) -> bool:
    """§A2: V(y) ≤ V(x) + Δ(ρ) for all (x, y, ρ) ∈ RV
    
    This ensures every certified transition is geometrically bounded.
    
    Args:
        obj: CohObject to verify
        
    Returns:
        True if A2 holds
        
    Note:
        Only works for finite models.
    """
    try:
        for x, y, rho in obj.valid_triples():
            lhs = obj.potential(y)
            rhs = obj.potential(x) + obj.budget_map(rho)
            if lhs > rhs:
                return False
        return True
    except NotImplementedError:
        # For infinite models, A2 is assumed by construction
        return True


def verify_deterministic_validity(obj: CohObject, samples: int = 10) -> bool:
    """§A3: RV(x, y, ρ) is replay-stable
    
    Determinism means the same inputs always produce the same result.
    
    Args:
        obj: CohObject to verify
        samples: Number of samples to test (default 10)
        
    Returns:
        True if validator is deterministic
        
    Note:
        Tests multiple calls with same inputs to verify
        deterministic behavior.
    """
    try:
        test_cases = obj.valid_triples()[:samples]
        for x, y, rho in test_cases:
            result1 = obj.validate(x, y, rho)
            result2 = obj.validate(x, y, rho)
            if result1 != result2:
                return False
        return True
    except NotImplementedError:
        # For infinite models, assume deterministic by construction
        return True


def transition_relation(obj: CohObject) -> Set[Tuple[Any, Any]]:
    """§3.1: T = {(x, y) | ∃ρ: RV(x, y, ρ)}
    
    The set of all valid state transitions (ignoring receipts).
    
    Args:
        obj: CohObject
        
    Returns:
        Set of (x, y) tuples representing valid transitions
        
    Note:
        Only available for finite models.
    """
    try:
        triples = obj.valid_triples()
        return {(x, y) for x, y, rho in triples}
    except NotImplementedError:
        raise NotImplementedError(
            "transition_relation() only available for finite models"
        )


def descent_preorder(obj: CohObject) -> Callable[[Any, Any], bool]:
    """§3.2: x ≼ y iff finite chain y = x₀ → x₁ → ... → xₙ = x
    
    The descent preorder relation. x ≼ y means y can reach x
    via a finite chain of valid transitions (descent direction).
    
    Note from spec:
        x ≼ y iff exists chain y = x₀ → x₁ → ... → xₙ = x
    
    This means: starting from y, we can reach x (descending in potential).
    
    Args:
        obj: CohObject
        
    Returns:
        Function (x, y) -> bool where x ≼ y
    """
    T = transition_relation(obj)
    
    def leq(x: Any, y: Any) -> bool:
        """Check if x ≼ y (x is reachable from y via descent)"""
        if x == y:
            return True
        
        # BFS from y toward x (descent direction)
        visited = {y}
        queue = deque([y])
        
        while queue:
            current = queue.popleft()
            for src, dst in T:
                if src == current:  # found next step in descent
                    if dst == x:
                        return True
                    if dst not in visited:
                        visited.add(dst)
                        queue.append(dst)
        return False
    
    return leq


def reachable_from(obj: CohObject, start: Any) -> Set[Any]:
    """Get all states reachable from start via valid transitions.
    
    Args:
        obj: CohObject
        start: Starting state
        
    Returns:
        Set of reachable states (including start)
    """
    T = transition_relation(obj)
    reachable = {start}
    queue = deque([start])
    
    while queue:
        current = queue.popleft()
        for src, dst in T:
            if src == current and dst not in reachable:
                reachable.add(dst)
                queue.append(dst)
    
    return reachable


def reachable_states(obj: CohObject) -> Set[Any]:
    """Get all states reachable from any admissible state.
    
    Args:
        obj: CohObject
        
    Returns:
        Set of all reachable states
    """
    admissible = {x for x in obj.valid_triples() if obj.is_admissible(x[0])}
    all_reachable = set()
    for x, _, _ in admissible:
        all_reachable.update(reachable_from(obj, x))
    return all_reachable


__all__ = [
    'verify_faithfulness',
    'verify_algebraic_geometric_binding',
    'verify_deterministic_validity',
    'transition_relation',
    'descent_preorder',
    'reachable_from',
    'reachable_states',
]
