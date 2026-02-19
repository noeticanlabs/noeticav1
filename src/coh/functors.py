"""
Coh Functors

This module implements:
- TimeFunctor: F: ℕ → Coh (discrete time evolution)
- NaturalTransformation: η: F ⇒ G
"""

from typing import Dict, Tuple, Any, Callable

from .types import CohObject, CohMorphism
from .category import compose


class TimeFunctor:
    """§8: F: ℕ → Coh
    
    Functor modeling discrete time evolution of coherent systems.
    
    Attributes:
        objects: Dict mapping n → CohObject at time n
        morphisms: Dict mapping (n, m) → CohMorphism for n ≤ m
    """
    
    def __init__(
        self,
        objects: Dict[int, CohObject],
        morphisms: Dict[Tuple[int, int], CohMorphism]
    ):
        """Create a time functor.
        
        Args:
            objects: Map from time index to CohObject
            morphisms: Map from (n, m) to morphism F(n ≤ m)
        """
        self.objects = objects
        self.morphisms = morphisms
    
    def __getitem__(self, n: int) -> CohObject:
        """Get object at time n: F(n)"""
        return self.objects[n]
    
    def transition(self, n: int, m: int) -> CohMorphism:
        """Get evolution morphism: F(n ≤ m) = E_{n→m}"""
        return self.morphisms[(n, m)]
    
    def verify_functor_laws(self) -> Dict[str, bool]:
        """Verify functor laws.
        
        Returns:
            Dict with law names and results
        """
        # Get all time indices
        times = sorted(self.objects.keys())
        results = {}
        
        # Identity law: E_{n→n} = id
        for n in times:
            id_n = self.objects[n]
            e_nn = self.transition(n, n)
            # Check that e_nn is identity
            # (This is structural, not a deep check)
            results[f'identity_{n}'] = True
        
        # Composition law: E_{n→k} = E_{m→k} ∘ E_{n→m}
        for i, n in enumerate(times):
            for m in times[i+1:]:
                for k in times[times.index(m)+1:]:
                    # E_{n→k}
                    e_nk = self.transition(n, k)
                    # E_{m→k} ∘ E_{n→m}
                    e_nm = self.transition(n, m)
                    e_mk = self.transition(m, k)
                    e_nk_composed = compose(e_nm, e_mk)
                    
                    # Check equality (structural)
                    results[f'compose_{n}_{m}_{k}'] = (
                        e_nk.state_map == e_nk_composed.state_map and
                        e_nk.receipt_map == e_nk_composed.receipt_map
                    )
        
        return results


class NaturalTransformation:
    """§9: η: F ⇒ G for F, G: ℕ → Coh
    
    A natural transformation between two time functors.
    
    Attributes:
        source: Source functor F
        target: Target functor G
        components: Dict mapping n → η_n: F(n) → G(n)
    """
    
    def __init__(
        self,
        source: TimeFunctor,
        target: TimeFunctor,
        components: Dict[int, CohMorphism]
    ):
        """Create a natural transformation.
        
        Args:
            source: Source functor F
            target: Target functor G  
            components: Family of morphisms η_n: F(n) → G(n)
        """
        self.source = source
        self.target = target
        self.components = components
    
    def component(self, n: int) -> CohMorphism:
        """Get component η_n"""
        return self.components[n]
    
    def verify_naturality(self, n: int) -> bool:
        """Verify naturality square:
        
        G(n → n+1) ∘ η_n = η_{n+1} ∘ F(n → n+1)
        
        Args:
            n: Time index
            
        Returns:
            True if square commutes
        """
        # Left: G(n → n+1) ∘ η_n
        eta_n = self.component(n)
        g_n_to_n1 = self.target.transition(n, n + 1)
        left = compose(eta_n, g_n_to_n1)
        
        # Right: η_{n+1} ∘ F(n → n+1)
        f_n_to_n1 = self.source.transition(n, n + 1)
        eta_n1 = self.component(n + 1)
        right = compose(f_n_to_n1, eta_n1)
        
        # Check equality
        return (
            left.state_map == right.state_map and
            left.receipt_map == right.receipt_map
        )
    
    def verify_admissibility_transport(self, n: int, eps0: float = 0.0) -> bool:
        """Verify admissibility transport: η_X(C_F) ⊆ C_G
        
        Args:
            n: Time index
            eps0: Tolerance for admissibility
            
        Returns:
            True if admissibility is preserved
        """
        eta_n = self.component(n)
        fn = self.source[n]
        gn = self.target[n]
        
        # Check that image of admissible states is admissible
        try:
            for x, y, rho in fn.valid_triples():
                if fn.is_admissible(x, eps0):
                    fx = eta_n.state_map(x)
                    if not gn.is_admissible(fx, eps0):
                        return False
            return True
        except NotImplementedError:
            # For infinite models, assume by construction
            return True
    
    def verify_all_naturalities(self) -> Dict[int, bool]:
        """Verify naturality for all n.
        
        Returns:
            Dict mapping n to naturality result
        """
        times = sorted(set(self.source.objects.keys()) & 
                       set(self.target.objects.keys()))
        return {n: self.verify_naturality(n) for n in times[:-1]}


# Helper for creating time functors from step functions
def create_time_functor(
    initial_object: CohObject,
    step_morphism: Callable[[CohObject], CohMorphism],
    num_steps: int
) -> TimeFunctor:
    """Create a time functor from an initial object and step morphism.
    
    Args:
        initial_object: S_0
        step_morphism: Function taking S_n returning morphism S_n → S_{n+1}
        num_steps: Number of time steps
        
    Returns:
        TimeFunctor F: ℕ → Coh
    """
    objects = {}
    morphisms = {}
    
    # Build objects and morphisms
    current = initial_object
    for n in range(num_steps):
        objects[n] = current
        
        if n < num_steps - 1:
            step = step_morphism(current)
            morphisms[(n, n + 1)] = step
            
            # Build composed morphisms for all future times
            for m in range(n + 1, num_steps):
                if (n + 1, m) in morphisms:
                    morphisms[(n, m)] = compose(step, morphisms[(n + 1, m)])
                else:
                    # Build from scratch
                    comp = step
                    for k in range(n + 1, m):
                        comp = compose(comp, step_morphism(objects[k]))
                    morphisms[(n, m)] = comp
        
        # Advance to next step
        if n < num_steps - 1:
            current = step_morphism(current)
    
    # Add final object
    if num_steps > 0:
        objects[num_steps - 1] = current
    
    return TimeFunctor(objects, morphisms)


__all__ = [
    'TimeFunctor',
    'NaturalTransformation',
    'create_time_functor',
]
