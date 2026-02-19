# Coh Morphisms

**Status:** Canonical  
**Section:** §4, §5

---

## Morphism Definition

A morphism:

```
f: S₁ → S₂
```

is a pair:

```
f = (f_X, f_♯)
```

where:
- **f_X**: X₁ → X₂ (state map)
- **f_♯**: Rec₁ → Rec₂ (receipt map)

---

## Morphism Axioms

### Axiom M1 — Admissibility Preservation

```
x ∈ C₁  ⇒  f_X(x) ∈ C₂
```

The image of an admissible state under the state map is admissible.

---

### Axiom M2 — Receipt Covariance

```
RV₁(x, y, ρ)  ⇒  RV₂(f_X(x), f_X(y), f_♯(ρ))
```

If receipt ρ certifies transition x → y in S₁, then the transported receipt certifies the mapped transition in S₂.

---

## Properties

### Proposition 5.1 — Order Preservation

If x ≼₁ y then f_X(x) ≼₂ f_X(y).

*Proof:* Apply M2 to each step in the chain. ∎

---

## Implementation Notes

### Type Signatures

```python
CohMorphism = {
    state_map: (x) -> x',    # f_X: X₁ → X₂
    receipt_map: (ρ) -> ρ'   # f_♯: Rec₁ → Rec₂
}
```

### Verification

```python
def verify_admissibility_preservation(f, dom, cod):
    """M1: x ∈ C₁ ⇒ f_X(x) ∈ C₂"""
    for x in dom.admissible:
        if not cod.is_admissible(f.state_map(x)):
            return False
    return True

def verify_receipt_covariance(f, dom, cod):
    """M2: RV₁(x,y,ρ) ⇒ RV₂(f_X(x),f_X(y),f_♯(ρ))"""
    # RV is represented as validate function
    for x, y, rho in dom.valid_triples():
        if not cod.validate(f.state_map(x), f.state_map(y), f.receipt_map(rho)):
            return False
    return True
```

---

## Conformance Points

| Axiom | Test |
|-------|------|
| M1 (Admissibility) | For all x ∈ C₁: f_X(x) ∈ C₂ |
| M2 (Receipt Covariance) | For all (x,y,ρ) ∈ RV₁: RV₂(f_X(x), f_X(y), f_♯(ρ)) |
| Order Preservation | x ≼₁ y ⇒ f_X(x) ≼₂ f_X(y) |

---

## Notes

- Morphisms preserve the categorical structure
- They transport algebraic witnesses (receipts) along with geometric states
- The composition of morphisms corresponds to sequential application of state and receipt maps
