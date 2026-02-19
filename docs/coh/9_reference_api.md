# Coh Reference API

**Status:** Reference  
**Purpose:** Runtime-facing Python API contract

---

## Overview

This document defines the public API for the **Coh** category implementation. All functions are pure where possible, with deterministic behavior required for replay verification.

---

## Core Types

### CohObject

```python
@dataclass(frozen=True)
class CohObject:
    """§1: An object is a 5-tuple (X, Rec, V, Δ, RV)"""
    
    is_state: Callable[[Any], bool]
    is_receipt: Callable[[Any], bool]
    potential: Callable[[Any], float]      # V: X → ℝ≥0
    budget_map: Callable[[Any], float]    # Δ: Rec → ℝ≥0
    validate: Callable[[Any, Any, Any], bool]  # RV(x, y, ρ)
```

### CohMorphism

```python
@dataclass(frozen=True)
class CohMorphism:
    """§4: A morphism is a pair (f_X, f_♯)"""
    
    state_map: Callable[[Any], Any]     # f_X: X₁ → X₂
    receipt_map: Callable[[Any], Any]   # f_♯: Rec₁ → Rec₂
```

---

## Object Functions

### is_admissible

```python
def is_admissible(obj: CohObject, x: Any, eps0: float = 0.0) -> bool:
    """§1.4: C = V^{-1}([0, ε₀]) with tolerance"""
    return obj.is_state(x) and obj.potential(x) <= eps0
```

**Parameters:**
- `obj`: CohObject
- `x`: state to check
- `eps0`: tolerance (default 0.0)

**Returns:** True if x is admissible

**Determinism:** Pure function, deterministic

---

### verify_faithfulness

```python
def verify_faithfulness(obj: CohObject) -> bool:
    """§A1: x ∈ C ⟺ V(x) = 0"""
    # For finite models only
    for x in obj.state_space:
        if obj.is_admissible(x, 0.0) != (obj.potential(x) == 0.0):
            return False
    return True
```

**Returns:** True if A1 holds

---

### verify_algebraic_geometric_binding

```python
def verify_algebraic_geometric_binding(obj: CohObject) -> bool:
    """§A2: V(y) ≤ V(x) + Δ(ρ) for all (x,y,ρ) ∈ RV"""
    # For finite models only
    for x, y, rho in obj.valid_triples():
        if obj.potential(y) > obj.potential(x) + obj.budget_map(rho):
            return False
    return True
```

**Returns:** True if A2 holds

---

### verify_deterministic_validity

```python
def verify_deterministic_validity(obj: CohObject) -> bool:
    """§A3: RV(x,y,ρ) is replay-stable"""
    test_cases = list(obj.valid_triples())[:10]
    for x, y, rho in test_cases:
        result1 = obj.validate(x, y, rho)
        result2 = obj.validate(x, y, rho)
        if result1 != result2:
            return False
    return True
```

**Returns:** True if validator is deterministic

---

### transition_relation

```python
def transition_relation(obj: CohObject) -> set:
    """§3.1: T = {(x,y) | ∃ρ: RV(x,y,ρ)}"""
    # For finite models only
    T = set()
    for x, y, rho in obj.valid_triples():
        T.add((x, y))
    return T
```

**Returns:** Set of (x, y) pairs

---

### descent_preorder

```python
def descent_preorder(obj: CohObject) -> Callable[[Any, Any], bool]:
    """§3.2: x ≼ y iff finite chain y = x₀ → x₁ → ... → xₙ = x"""
    T = transition_relation(obj)
    
    def leq(x, y):
        if x == y:
            return True
        # BFS from y toward x (descent direction)
        visited = {y}
        queue = [y]
        while queue:
            current = queue.pop(0)
            for src, dst in T:
                if src == current:
                    if dst == x:
                        return True
                    if dst not in visited:
                        visited.add(dst)
                        queue.append(dst)
        return False
    
    return leq
```

**Returns:** Function (x, y) -> bool for preorder

---

## Morphism Functions

### verify_admissibility_preservation

```python
def verify_admissibility_preservation(
    f: CohMorphism, 
    dom: CohObject, 
    cod: CohObject
) -> bool:
    """§M1: x ∈ C₁ ⇒ f_X(x) ∈ C₂"""
    for x in dom.state_space:
        if dom.is_admissible(x, 0.0):
            if not cod.is_admissible(f.state_map(x), 0.0):
                return False
    return True
```

**Returns:** True if M1 holds

---

### verify_receipt_covariance

```python
def verify_receipt_covariance(
    f: CohMorphism,
    dom: CohObject,
    cod: CohObject
) -> bool:
    """§M2: RV₁(x,y,ρ) ⇒ RV₂(f_X(x),f_X(y),f_♯(ρ))"""
    for x, y, rho in dom.valid_triples():
        if not cod.validate(
            f.state_map(x), 
            f.state_map(y), 
            f.receipt_map(rho)
        ):
            return False
    return True
```

**Returns:** True if M2 holds

---

## Category Functions

### identity

```python
def identity(obj: CohObject) -> CohMorphism:
    """§6.1: id_S = (id_X, id_Rec)"""
    return CohMorphism(
        state_map=lambda x: x,
        receipt_map=lambda rho: rho
    )
```

**Returns:** Identity morphism

---

### compose

```python
def compose(f: CohMorphism, g: CohMorphism) -> CohMorphism:
    """§6.2: g ∘ f = (g_X ∘ f_X, g_♯ ∘ f_♯)"""
    return CohMorphism(
        state_map=lambda x: g.state_map(f.state_map(x)),
        receipt_map=lambda rho: g.receipt_map(f.receipt_map(rho))
    )
```

**Parameters:**
- `f`: first morphism (domain to codomain)
- `g`: second morphism (domain to codomain)

**Returns:** Composed morphism

**Note:** Does not verify M1/M2. Use `compose_checked` for verification.

---

### compose_checked

```python
def compose_checked(
    f: CohMorphism, 
    g: CohMorphism,
    dom: CohObject,
    mid: CohObject,
    cod: CohObject
) -> CohMorphism:
    """Compose with axiom verification"""
    result = compose(f, g)
    
    assert verify_admissibility_preservation(result, dom, cod), "M1 failed"
    assert verify_receipt_covariance(result, dom, cod), "M2 failed"
    
    return result
```

**Raises:** AssertionError if axioms fail

---

## Limit Functions

### product

```python
def product(obj1: CohObject, obj2: CohObject) -> CohObject:
    """§7.1: X_× = X₁ × X₂, V_×(x₁,x₂) = V₁(x₁) + V₂(x₂)"""
    # Implementation in limits.py
    pass
```

**Returns:** Product object

---

### pullback

```python
def pullback(
    A: CohObject,
    B: CohObject,
    p: CohMorphism,
    l: CohMorphism
) -> CohObject:
    """§7.2: X_pb = {(a,b) | p_X(a) = l_X(b)}"""
    # Implementation in limits.py
    pass
```

**Returns:** Pullback object

---

## Functor Functions

### TimeFunctor

```python
class TimeFunctor:
    """§8: F: ℕ → Coh"""
    
    def __init__(self, objects: Dict[int, CohObject], 
                 morphisms: Dict[Tuple[int, int], CohMorphism]):
        self.objects = objects
        self.morphisms = morphisms
    
    def __getitem__(self, n: int) -> CohObject:
        return self.objects[n]
    
    def transition(self, n: int, m: int) -> CohMorphism:
        """F(n ≤ m) = E_{n→m}"""
        return self.morphisms[(n, m)]
```

---

### NaturalTransformation

```python
class NaturalTransformation:
    """§9: η: F ⇒ G for F,G: ℕ → Coh"""
    
    def __init__(self, source: TimeFunctor, target: TimeFunctor,
                 components: Dict[int, CohMorphism]):
        self.source = source
        self.target = target
        self.components = components
    
    def verify_naturality(self, n: int) -> bool:
        """G(n→n+1) ∘ η_n = η_{n+1} ∘ F(n→n+1)"""
        left = compose(self.components[n], 
                        self.target.transition(n, n+1))
        right = compose(self.source.transition(n, n+1),
                        self.components[n+1])
        return left == right
```

---

## Hashing and Determinism

### Requirements

All callable components must be:
1. **Pure**: no side effects
2. **Hashable inputs**: states and receipts must be hashable
3. **Canonical**: same logical value → same representation

### Canonicalization

```python
def canonicalize(obj: CohObject) -> CohObject:
    """Ensure deterministic representation"""
    return CohObject(
        is_state=obj.is_state,
        is_receipt=obj.is_receipt,
        potential=obj.potential,
        budget_map=obj.budget_map,
        validate=obj.validate
    )
```

---

## Error Handling

| Function | Error | Cause |
|----------|-------|-------|
| transition_relation | NotImplementedError | Called on infinite state space |
| valid_triples | NotImplementedError | Called on infinite state space |
| verify_* | ValueError | Finite model required |
| compose_checked | AssertionError | Axiom M1 or M2 fails |

---

## Version

- **Coh API v1.0**: Initial release
- Changes require explicit version bump
