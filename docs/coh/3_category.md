# Coh Category Structure

**Status:** Canonical  
**Section:** §6

---

## Category Axioms

**Coh** forms a category with:

1. Objects: CohObject (§1)
2. Morphisms: CohMorphism (§4)
3. Identity and composition satisfying category laws

---

## Identity Morphism

For each object S, the identity morphism is:

```
id_S = (id_X, id_Rec)
```

where:
- id_X: X → X is the identity function on states
- id_Rec: Rec → Rec is the identity function on receipts

Satisfies M1 and M2 trivially.

---

## Composition

For morphisms:

```
f: S₁ → S₂  = (f_X, f_♯)
g: S₂ → S₃  = (g_X, g_♯)
```

Define composition:

```
g ∘ f = (g_X ∘ f_X, g_♯ ∘ f_♯)
```

The receipt map composes by substitution.

---

## Associativity

Composition is associative:

```
(h ∘ g) ∘ f = h ∘ (g ∘ f)
```

Follows from function composition associativity.

---

## Category Laws

| Law | Expression |
|-----|------------|
| Identity left | id ∘ f = f |
| Identity right | f ∘ id = f |
| Associativity | (h ∘ g) ∘ f = h ∘ (g ∘ f) |

---

## Implementation Notes

```python
class CohCategory:
    def id(self, obj: CohObject) -> CohMorphism:
        """§6.1: id_S = (id_X, id_Rec)"""
        return CohMorphism(
            state_map=lambda x: x,
            receipt_map=lambda rho: rho
        )
    
    def compose(self, f: CohMorphism, g: CohMorphism) -> CohMorphism:
        """§6.2: g ∘ f = (g_X ∘ f_X, g_♯ ∘ f_♯)"""
        return CohMorphism(
            state_map=lambda x: g.state_map(f.state_map(x)),
            receipt_map=lambda rho: g.receipt_map(f.receipt_map(rho))
        )
```

---

## Checked Composition

For testing and verification, use composition that validates axioms:

```python
def compose_checked(f, g, dom, mid, cod):
    """Compose with axiom verification"""
    result = compose(f, g)
    
    # Verify M1: admissibility preserved
    assert verify_admissibility_preservation(result, dom, cod)
    
    # Verify M2: receipt covariance
    assert verify_receipt_covariance(result, dom, cod)
    
    return result
```

---

## Conformance Points

| Law | Test |
|-----|------|
| Identity left | id ∘ f = f |
| Identity right | f ∘ id = f |
| Associativity | (h ∘ g) ∘ f = h ∘ (g ∘ f) |

---

## Notes

- The category structure ensures coherent composition of systems
- Morphisms preserve the algebraic-geometric binding (A2)
- Time evolution (functors) compose within this category structure
