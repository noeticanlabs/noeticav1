# Coh Built-in Functors

**Status:** Canonical  
**Section:** §2 (Derived Structures)

---

## Overview

Several important functors can be defined on **Coh** that extract specific structural information. These are the "forgetful" or "projection" functors that map Coh objects to more primitive mathematical structures.

---

## Violation Functor (Vio)

```
Vio: Coh → Set^ℝ≥0
```

Maps a Coh object to its potential functional:

```
Vio(S) = (X → V)
```

Where Set^ℝ≥0 is the category of sets equipped with a function to ℝ≥0.

### Definition

```python
def vio_functor(obj: CohObject) -> Callable[[Any], float]:
    """Vio: Coh → Set^ℝ≥0, S ↦ (X → V)"""
    return obj.potential
```

### Properties

- Faithful: different objects may have same V
- Preserves products: Vio(S₁ × S₂) = Vio(S₁) + Vio(S₂)

---

## Admissible Set Functor (Adm)

```
Adm: Coh → Set
```

Maps a Coh object to its admissible set:

```
Adm(S) = C = V⁻¹(0)
```

### Definition

```python
def adm_functor(obj: CohObject, eps0: float = 0.0) -> set:
    """Adm: Coh → Set, S ↦ C = V^{-1}([0, ε₀])"""
    return {x for x in obj.state_space if obj.potential(x) <= eps0}
```

### Properties

- Subset of state space
- Closed (by lower semicontinuity of V)
- Preserved by morphisms (M1)

---

## Transition Functor (Trans)

```
Trans: Coh → Graph
```

Maps a Coh object to its transition relation as a directed graph:

```
Trans(S) = (X, T) where T = {(x,y) | ∃ρ: RV(x,y,ρ)}
```

### Definition

```python
def transition_functor(obj: CohObject) -> DiGraph:
    """Trans: Coh → Graph, S ↦ (X, T)"""
    T = obj.transition_relation()
    # Returns graph structure for reachability analysis
    return create_digraph(nodes=obj.state_space, edges=T)
```

### Properties

- Nodes are states
- Edges are certified transitions
- Supports reachability analysis (descent preorder)

---

## Budget Functor (Budget)

```
Budget: Coh → Set^ℝ≥0
```

Maps a Coh object to its budget map:

```
Budget(S) = (Rec → Δ)
```

### Definition

```python
def budget_functor(obj: CohObject) -> Callable[[Any], float]:
    """Budget: Coh → Set^ℝ≥0, S ↦ (Rec → Δ)"""
    return obj.budget_map
```

---

## Combined Projection

A combined projection maps to a tuple:

```python
def project(obj: CohObject):
    """Combined projection"""
    return (
        obj.state_space,
        obj.receipt_set,
        obj.potential,
        obj.budget_map,
        obj.admissible,
        obj.transition_relation()
    )
```

---

## Functor Composition

These functors compose:

```
Adm ∘ Trans: Coh → Set
```

gives the set of states reachable from admissible states.

---

## Implementation Notes

```python
class CohFunctors:
    """Collection of built-in Coh functors"""
    
    @staticmethod
    def Vio(obj):
        """Violation functor"""
        return obj.potential
    
    @staticmethod
    def Adm(obj, eps0=0.0):
        """Admissible set functor"""
        return {x for x in obj.state_space if obj.potential(x) <= eps0}
    
    @staticmethod
    def Trans(obj):
        """Transition relation as graph"""
        return obj.transition_relation()
    
    @staticmethod
    def Budget(obj):
        """Budget map"""
        return obj.budget_map
```

---

## Conformance Points

| Functor | Mapping | Properties |
|---------|---------|------------|
| Vio | S ↦ (X → V) | Preserves products |
| Adm | S ↦ C = V⁻¹(0) | Preserved by morphisms |
| Trans | S ↦ (X, T) | Supports reachability |
| Budget | S ↦ (Rec → Δ) | Composes with Vio |

---

## Notes

- These functors provide the "forgetful" maps that expose internal structure
- They are essential for analysis and verification
- Products and pullbacks in Coh induce corresponding operations in these functors' codomains
