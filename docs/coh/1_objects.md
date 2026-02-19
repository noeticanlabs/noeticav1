# Coh Objects

**Canonical ID:** `coh.category.v1`  
**Status:** Canonical  
**Section:** §1, §2

---

## Object Definition

An object of **Coh** can be represented in two equivalent forms:

### 5-tuple form (canonical)

```
S = (X, Rec, V, Δ, RV)
```

### 3-tuple form (spec v1.0.0 simplified)

```
S = (X, V, RV)
```

Where the budget map Δ is implicitly handled within RV.

Both forms are equivalent — the 5-tuple makes the components explicit, while the 3-tuple is the simplified engineering form from the spec.

**Component definitions below apply to both forms.**

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

## 1.7 Bounded-Tube Admissibility (Practical Regime)

**Specification v1.0.0 — §3.2**

In addition to zero-set admissibility (strict), Coh supports bounded-tube admissibility for systems where "valid" means "within tolerance."

### Definition

Fix a threshold Θ > 0. Define:

```
C_S(Θ) := {x ∈ X : V(x) ≤ Θ}
```

This is the **bounded tube** around the admissible set.

### Faithfulness Axiom (Bounded)

```
x ∈ C_S(Θ)  ⟺  V(x) ≤ Θ
```

### When to Use Bounded-Tube

| Regime | Use Case | Example |
|--------|----------|---------|
| Zero-set (strict) | Type soundness, ledger invariants | Exact constraints |
| Bounded-tube | Physical sensors, PDE, noisy control | Within tolerance |

### Canon Rule

Every Coh object must declare:
- Which admissibility regime it uses (strict or bounded)
- If bounded, the threshold Θ value

### Implementation

```python
def bounded_admissible(obj, x, theta):
    """Check if x is within the bounded tube of admissibility."""
    return obj.is_state(x) and obj.potential(x) <= theta
```

---

## Conformance Points

| Axiom | Test |
|-------|------|
| A1 (Faithfulness) | Verify C = {x | V(x) = 0} |
| A2 (Binding) | For all (x,y,ρ) in RV: V(y) ≤ V(x) + Δ(ρ) |
| A3 (Determinism) | Multiple calls to validate with same inputs return same outputs |

---

---

## 1.8 Implementation Contract

**Specification v1.0.0 — §11**

To claim an implementation "is a Coh object," the module must define:

### Required Components

| Component | Description | Spec Reference |
|-----------|-------------|----------------|
| `state_space` | Canonical type representation of X | §2.1 |
| `potential` | Deterministic evaluator V(x) | §2.2 |
| `receipt_schema` | Canonical serialization and required fields | §4.2 |
| `verifier` | Deterministic RV(x, r, x') | §2.3 |
| `canon_profile` | Numeric representation, rounding rules, hash rules | §7 |

### Type Signatures (Extended)

```python
# Full implementation contract for Coh objects
class CohObject(Protocol):
    """Coh Object Implementation Contract"""
    
    # State space representation
    def is_state(self, x: Any) -> bool:
        """Check if x is a valid state in X."""
        ...
    
    # Potential functional (faithfulness)
    def potential(self, x: Any) -> float:
        """V: X → ℝ≥0 - distance to validity."""
        ...
    
    # Receipt handling
    def is_receipt(self, r: Any) -> bool:
        """Check if r is a valid receipt."""
        ...
    
    # Verifier predicate (deterministic)
    def validate(self, x: Any, r: Any, x_prime: Any) -> bool:
        """
        RV(x, r, x') → {ACCEPT, REJECT}
        Must be deterministic: same inputs → same output.
        """
        ...
    
    # Optional: Admissibility regime
    def admissibility_regime(self) -> str:
        """Returns 'strict' or 'bounded'."""
        ...
    
    def threshold(self) -> float:
        """Returns Θ if bounded regime, else ignored."""
        ...
```

### Canon Profile Requirements

The `canon_profile` must specify:

1. **Serialization**: Canonical JSON (RFC 8785 JCS) or frozen binary
2. **Normalization**: UTF-8 NFC for text fields
3. **Key Ordering**: Fixed (e.g., lexicographical)
4. **Numeric Domain**: One of:
   - Scaled integers (QFixed)
   - Integer rationals (bigint numerator/denominator)
   - Interval arithmetic over scaled integers

---

## Notes

- Acyclicity requires strict descent: V(y) < V(x) for all nontrivial transitions.
- Without strict descent, cycles at constant potential are allowed.
