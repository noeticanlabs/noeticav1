# Coh Functors

**Canonical ID:** `coh.category.v1`  
**Status:** Canonical  
**Section:** §8, §9

---

## Functorial Time

Define a functor:

```
F: ℕ → Coh
```

This models discrete time evolution of coherent systems.

### Objects

```
F(n) = S_n
```

Each time step n has an associated coherent object.

### Morphisms

```
F(n ≤ m) = E_{n→m}
```

with:

```
E_{n→m} = (E_X, E_♯)
```

- E_X: state evolution over time
- E_♯: receipt composition over time

---

## Functor Laws

### Identity

```
E_{n→n} = (id_X, id_Rec)
```

### Composition

```
E_{n→k} = E_{m→k} ∘ E_{n→m}
```

including receipt composition:

```
(E_♯)_{n→k} = (E_♯)_{m→k} ∘ (E_♯)_{n→m}
```

If receipt composition fails, the time functor does not exist.

---

## Natural Transformations

Let:

```
F, G: ℕ → Coh
```

be two time functors.

A natural transformation:

```
η: F ⇒ G
```

is a family of morphisms:

```
η_n = (η_X, η_♯): F(n) → G(n)
```

satisfying the naturality square:

```
G(n → n+1) ∘ η_n = η_{n+1} ∘ F(n → n+1)
```

 diagrammatically:

```
F(n) ---η_n---> G(n)
  |                 |
F(n→n+1)         G(n→n+1)
  |                 |
  v                 v
F(n+1)-η_{n+1}-> G(n+1)
```

### Admissibility Transport

Because each η_n satisfies M1:

```
η_X(C_F) ⊆ C_G
```

Admissibility is preserved under natural transformations (upgrades).

---

## Implementation Notes

### Time Functor

```python
class TimeFunctor:
    """F: ℕ → Coh"""
    
    def __init__(self, objects, morphisms):
        self.objects = objects      # dict: n -> CohObject
        self.morphisms = morphisms  # dict: (n, m) -> CohMorphism
    
    def __getitem__(self, n):
        return self.objects[n]
    
    def transition(self, n, m):
        """F(n ≤ m) = E_{n→m}"""
        return self.morphisms[(n, m)]
    
    # Functor laws verified:
    # - id: E_{n→n} = (id_X, id_Rec)
    # - compose: E_{n→k} = E_{m→k} ∘ E_{n→m}
```

### Natural Transformation

```python
class NaturalTransformation:
    """η: F ⇒ G for F,G: ℕ → Coh"""
    
    def __init__(self, source, target, components):
        self.source = source      # TimeFunctor
        self.target = target      # TimeFunctor
        self.components = components  # dict: n -> CohMorphism
    
    def verify_naturality(self, n):
        """G(n→n+1) ∘ η_n = η_{n+1} ∘ F(n→n+1)"""
        left = compose(
            self.components[n],
            self.target.transition(n, n+1)
        )
        right = compose(
            self.source.transition(n, n+1),
            self.components[n+1]
        )
        return left == right
    
    def verify_admissibility_transport(self, n):
        """η_X(C_F) ⊆ C_G"""
        eta = self.components[n]
        source_adm = self.source[n].admissible
        target_adm = self.target[n].admissible
        return all(eta.state_map(x) in target_adm for x in source_adm)
```

---

## Conformance Points

| Property | Test |
|----------|------|
| Functor identity | E_{n→n} = (id_X, id_Rec) |
| Functor composition | E_{n→k} = E_{m→k} ∘ E_{n→m} |
| Naturality square | G(n→n+1) ∘ η_n = η_{n+1} ∘ F(n→n+1) |
| Admissibility transport | η_X(C_F) ⊆ C_G |

---

## Notes

- Functorial time ensures deterministic, composable system evolution
- Natural transformations model "upgrades" that preserve coherence
- The time functor is the categorical foundation for NK-2 scheduler semantics
