# Categorical Spine: Coh–PoC–LoC

This document provides a formal overview of the categorical architecture underlying the Noetica system. It connects the mathematical theory to the code structure.

---

## 1. Core Definitions

### 1.1 Coh Object

A **Coh object** is a 5-tuple:

```
A = (X, Rec, V, Δ, RV)
```

Where:
- `X`: State space (set of possible states)
- `Rec`: Receipt set (algebraic witnesses)
- `V: X → ℝ≥0`: Coherence functional (violation measure)
- `Δ: Rec → ℝ≥0`: Budget allowance map
- `RV ⊆ X × X × Rec`: Valid transition relation

The admissible states are:

```
C = { x ∈ X | V(x) ≤ ε₀ }
```

### 1.2 Coh Morphism

A **Coh morphism** `f: A → B` is a pair:

```
f = (f_X, f_♯)
```

Where:
- `f_X: X_A → X_B`: State map
- `f_♯: Rec_A → Rec_B`: Receipt map

With properties:
- **M1 (Admissibility preservation)**: `x ∈ C_A ⇒ f_X(x) ∈ C_B`
- **M2 (Receipt covariance)**: `RV_A(x,y,ρ) ⇒ RV_B(f_X(x), f_X(y), f_♯(ρ))`

---

## 2. Oplax Proof Functor

### 2.1 Definition

The oplax proof functor measures authority spent:

```
|f|_V := inf{ spent(π) | V(desc(f), π) = Accept }
```

In practice (Regime B), we use deterministic cost extraction:

```
|f|_V = spent(π_f)
```

where `π_f` is the canonical receipt for transition `f`.

### 2.2 Budget Rule

For a transition `f: A → B` with pre-budget `b` and post-budget `b'`:

```
b' = b - |f|_V
```

Or equivalently, the morphism exists iff:

```
b ≥ b' + |f|_V
```

This is the **Grothendieck pullback**:

```
f*(b') = b' + |f|_V
```

---

## 3. Cost Model (Regime B)

### 3.1 Bounded Violation

Under bounded PoC (Regime B), we allow limited violation increase:

```
C(x') ≤ C(x) + Δ_max
```

Where the excess violation triggers proportional cost.

### 3.2 Cost Formula

```
verification_cost(f) = base_fee + λ * Δ⁺ + penalties
```

Where:
- `base_fee`: Fixed verification overhead
- `λ`: Global governance stiffness (protocol constant)
- `Δ⁺ = max(0, C(x') - C(x))`: Excess violation
- `penalties`: Policy-specific penalty amounts

### 3.3 Subadditivity

The oplax structure satisfies:

```
|g ∘ f|_V ≤ |f|_V + |g|_V
```

This guarantees compositionality - stacking transitions is safe.

---

## 4. Monoidal Structure

### 4.1 Tensor Product

The **additive tensor product**:

```
A ⊗ B = (X_A × X_B, C_A × C_B, V_A + V_B)
```

Properties:
- **Faithfulness**: `V(x,y) = 0 ⟺ V_A(x) = 0 ∧ V_B(y) = 0`
- **Non-inflation**: `(f ⊗ g)` preserves non-inflation
- **Additivity**: `|f ⊗ g| = |f| + |g|`

### 4.2 Unit Object

```
I = ({*}, {*}, 0)
```

Satisfies: `I ⊗ A ≅ A`

### 4.3 Symmetry

```
σ: A ⊗ B → B ⊗ A
σ(x, y) = (y, x)
```

---

## 5. Code Structure

### 5.1 Core Modules

| Module | Purpose |
|--------|---------|
| `src/coh/types.py` | `CohObject`, `CohMorphism` definitions |
| `src/coh/scalar.py` | CK-0 scalar `C(x)` computation |
| `src/coh/objects.py` | Axiom verification (A1, A2, A3) |
| `src/coh/morphisms.py` | Morphism verification (M1, M2) |
| `src/coh/limits.py` | Products and pullbacks |
| `src/coh/tensor.py` | Monoidal tensor product |
| `src/coh/grothendieck.py` | Budget pullback |
| `src/ck0/cost.py` | Governance cost functions |

### 5.2 Usage Example

```python
from coh.types import CohObject, CohMorphism
from coh.scalar import compute_ck0_scalar
from ck0.cost import verification_cost, CostConfig
from coh.grothendieck import Budget, morphism_exists

# Create cost config
config = CostConfig(base_fee=0, lambda_global=1)

# Check if transition is valid
budget_before = Budget(100)
budget_after = Budget(95)  # spent 5

if morphism_exists(f, budget_before, budget_after, config):
    print("Transition valid under budget!")
```

---

## 6. Global vs Instance Morphism

### 6.1 Global Morphism Property

A **global morphism** satisfies:

```
V_B(f(x)) ≤ V_A(x)  ∀x ∈ X_A
```

This is a design-time property of the morphism structure.

### 6.2 Instance Certification

An **instance morphism** is a specific executed transition:

```
f: x → x' with receipt π
```

Verified by NK-4G: checks the specific `x`, `x'`, `π` triple.

### 6.3 Operational Coh_rcpt

The runtime uses the **receipt-discipline variant** (`Coh_rcpt`):
- Deterministic receipts
- No retry (subadditivity enforceable)
- Instance verification only

---

## 7. References

- `plans/coh_structural_audit_implementation_plan.md` - Implementation details
- `docs/coh/0_overview.md` - Category overview
- `docs/coh/1_objects.md` - Object axioms
- `docs/coh/2_morphisms.md` - Morphism axioms
- `docs/ck0/3_violation_functional.md` - V(x) definition
- `docs/ck0/4_budget_debt_law.md` - Budget law
