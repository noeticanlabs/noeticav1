"""
Coh Built-in Functors

This module defines important functors that extract structural
information from Coh objects.
"""

from typing import Callable, Any, Set, Dict

from .types import CohObject


class ViolationFunctor:
    """Vio: Coh → Set^ℝ≥0
    
    Maps a Coh object to its potential functional.
    """
    
    @staticmethod
    def map(obj: CohObject) -> Callable[[Any], float]:
        """Vio(S) = (X → V)"""
        return obj.potential
    
    @staticmethod
    def apply(obj: CohObject, x: Any) -> float:
        """Apply to a specific state"""
        return obj.potential(x)


class AdmissibleFunctor:
    """Adm: Coh → Set
    
    Maps a Coh object to its admissible set.
    """
    
    @staticmethod
    def map(obj: CohObject, eps0: float = 0.0) -> Set[Any]:
        """Adm(S) = C = V^{-1}([0, ε₀])"""
        try:
            return {
                x for x, y, rho in obj.valid_triples()
                if obj.is_admissible(x, eps0)
            }
        except NotImplementedError:
            raise NotImplementedError(
                "AdmissibleFunctor only works for finite models"
            )
    
    @staticmethod
    def contains(obj: CohObject, x: Any, eps0: float = 0.0) -> bool:
        """Check if x is in admissible set"""
        return obj.is_admissible(x, eps0)


class TransitionFunctor:
    """Trans: Coh → Graph
    
    Maps a Coh object to its transition relation as a graph.
    """
    
    @staticmethod
    def map(obj: CohObject) -> Set[tuple]:
        """Trans(S) = T = {(x,y) | ∃ρ: RV(x,y,ρ)}"""
        try:
            return obj.transition_relation()
        except NotImplementedError:
            raise NotImplementedError(
                "TransitionFunctor only works for finite models"
            )
    
    @staticmethod
    def nodes(obj: CohObject) -> Set[Any]:
        """Get all states (nodes) in the transition graph"""
        T = TransitionFunctor.map(obj)
        nodes = set()
        for x, y in T:
            nodes.add(x)
            nodes.add(y)
        return nodes
    
    @staticmethod
    def edges(obj: CohObject) -> Set[tuple]:
        """Get all transitions (edges) in the graph"""
        return TransitionFunctor.map(obj)


class BudgetFunctor:
    """Budget: Coh → Set^ℝ≥0
    
    Maps a Coh object to its budget map.
    """
    
    @staticmethod
    def map(obj: CohObject) -> Callable[[Any], float]:
        """Budget(S) = (Rec → Δ)"""
        return obj.budget_map
    
    @staticmethod
    def apply(obj: CohObject, rho: Any) -> float:
        """Apply to a specific receipt"""
        return obj.budget_map(rho)


class ValidatorFunctor:
    """Val: Coh → (X × X × Rec → Bool)
    
    Maps a Coh object to its validator function.
    """
    
    @staticmethod
    def map(obj: CohObject) -> Callable[[Any, Any, Any], bool]:
        """Val(S) = RV"""
        return obj.validate
    
    @staticmethod
    def apply(obj: CohObject, x: Any, y: Any, rho: Any) -> bool:
        """Apply validator to a triple"""
        return obj.validate(x, y, rho)


# Combined projection
class Projector:
    """Combined projection from Coh to tuple of structures"""
    
    @staticmethod
    def project(obj: CohObject) -> Dict[str, Any]:
        """Combined projection"""
        result = {
            'potential': obj.potential,
            'budget_map': obj.budget_map,
            'validate': obj.validate,
        }
        
        try:
            result['admissible'] = AdmissibleFunctor.map(obj)
            result['transition_relation'] = TransitionFunctor.map(obj)
        except NotImplementedError:
            pass
        
        return result


# Functor composition helpers
def compose_vio_adm(obj: CohObject, eps0: float = 0.0) -> Set[float]:
    """Adm ∘ Vio: Get all potential values for admissible states
    
    Args:
        obj: CohObject
        eps0: Tolerance for admissibility
        
    Returns:
        Set of potential values
    """
    adm = AdmissibleFunctor.map(obj, eps0)
    return {obj.potential(x) for x in adm}


def compose_trans_reachable(obj: CohObject) -> Set[Any]:
    """Trans → reachable: All states reachable from admissible
    
    Returns:
        Set of all reachable states
    """
    try:
        from .objects import reachable_states
        return reachable_states(obj)
    except NotImplementedError:
        raise NotImplementedError(
            "compose_trans_reachable only works for finite models"
        )


__all__ = [
    'ViolationFunctor',
    'AdmissibleFunctor', 
    'TransitionFunctor',
    'BudgetFunctor',
    'ValidatorFunctor',
    'Projector',
    'compose_vio_adm',
    'compose_trans_reachable',
]
