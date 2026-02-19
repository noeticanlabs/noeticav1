# Coh Objects

**Status:** Canonical  
**Section:** §1, §2

---

## Object Definition

An object of **Coh** is a 5-tuple:

```
S = (X, Rec, V, Δ, RV)
```

where each component is defined below.

---

## 1.1 State Space (X)

**X** is a set representing the geometric state space.

Optionally:
- Topological space
- Measurable space
- Smooth manifold
- Discrete lattice

No additional structure is required for categorical validity.

---

## 1.2 Receipt Set (Rec)

**Rec** is a set of algebraic witnesses.

Elements ρ ∈ Rec represent computational, analytic, or cryptographic proofs of validity.

---

## 1.3 Potential Functional (V)

**V**: X → ℝ≥0

A lower semicontinuous function mapping states to non-negative real numbers.

---

## 1.4 Admissible Set (C)

**C** = V⁻¹(0)

Because V is lower semicontinuous, C is closed.

---

## 1.5 Budget Map (Δ)

**Δ**: Rec → ℝ≥0

Assigns to each receipt a permitted violation allowance.

**Special case**: Strict descent systems use Δ ≡ 0.

---

## 1.6 Validator Relation (RV)

**RV** ⊆ X × X × Rec

Write RV(x, y, ρ) to mean receipt ρ certifies transition x → y.

---

## Object Axioms

### Axiom A1 — Faithfulness

Admissibility is defined exactly by:

```
x ∈ C  ⟺  V(x) = 0
```

---

### Axiom A2 — Algebraic–Geometric Binding

For all (x, y, ρ) ∈ RV:

```
V(y) ≤ V(x) + Δ(ρ)
```

This ensures every certified transition is geometrically bounded.

---

### Axiom A3 — Deterministic Validity

RV(x, y, ρ) is replay-stable.

Determinism means:
- The validator is a pure function
- Canonical serialization ensures reproducible inputs

---

## Derived Structures

### Transition Relation (§3.1)

```
T = {(x, y) | ∃ρ: RV(x, y, ρ)}
```

### Descent Preorder (§3.2)

Define x ≼ y iff there exists a finite chain:

```
y = x₀ → x₁ → ⋯ → xₙ = x
```

with (xᵢ, xᵢ₊₁) ∈ T.

**Proposition 3.1 — Preorder**

≼ is reflexive and transitive.

*Proof:* Reflexive via zero-length chain. Transitive via chain concatenation. ∎

---

## Implementation Notes

### Type Signatures

```python
# Abstract carriers for infinite/continuous state spaces
CohObject = {
    is_state: (x) -> bool,
    is_receipt: (ρ) -> bool,
    potential: (x) -> float,      # V: X → ℝ≥0
    budget_map: (ρ) -> float,       # Δ: Rec → ℝ≥0
    validate: (x, y, ρ) -> bool    # RV(x, y, ρ)
}
```

### Admissibility

```python
def admissible(obj, x, eps0=0.0):
    return obj.is_state(x) and obj.potential(x) <= eps0
```

---

## Conformance Points

| Axiom | Test |
|-------|------|
| A1 (Faithfulness) | Verify C = {x | V(x) = 0} |
| A2 (Binding) | For all (x,y,ρ) in RV: V(y) ≤ V(x) + Δ(ρ) |
| A3 (Determinism) | Multiple calls to validate with same inputs return same outputs |

---

## Notes

- Acyclicity requires strict descent: V(y) < V(x) for all nontrivial transitions.
- Without strict descent, cycles at constant potential are allowed.
