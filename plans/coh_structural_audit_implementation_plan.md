# Coh–PoC–LoC Structural Audit Implementation Plan

**Status:** Implementation Plan  
**Generated:** 2026-02-19  
**Based on:** Hostile Architecture Audit  
**Mode:** 🏗️ Architect

---

## Executive Summary

This plan addresses the structural gaps identified in the hostile audit between the mathematical theory (Coh–PoC–LoC) and the repository implementation. The audit correctly identified that while the conceptual alignment is solid, the categorical abstraction layer is not yet first-class in code.

**Key Decisions (per clarifications):**
- **Tensor Product**: Additive tensor `V(x,y) = V_A(x) + V_B(y)` (not max or product)
- **PoC Regime**: Bounded violation (Regime B) allowing Δ⁺ with proportional cost
- **λ (Governance Stiffness)**: Global fixed constant for compositionality guarantees

---

## 1️⃣ Gap Analysis

| Gap # | Audit Finding | Current State | Required Action |
|-------|--------------|---------------|------------------|
| 1 | CohObject not first-class | `src/coh/types.py` has `CohObject` dataclass | Already exists ✓ |
| 2 | CK-0 scalar not unified | Scattered in budget_law, violation.py | Create `src/coh/scalar.py` |
| 3 | Budget pullback not explicit | Implicit in NK-2 execution | Create `src/coh/grothendieck.py` |
| 4 | Global vs instance morphism | Not documented | Add docs + type distinction |
| 5 | Monoidal structure not represented | Product exists, no tensor | Create `src/coh/tensor.py` |
| 6 | verification_cost() not canonical | Embedded in logic | Create `src/ck0/cost.py` |
| 7 | No formal docs page | Scattered docs | Create `docs/categorical_spine.md` |
| 8 | No QFixed determinism tests | Implicit assumption | Add test suite |

---

## 2️⃣ Mathematical Definitions (Canon)

### 2.1 Additive Tensor Product

```python
# src/coh/tensor.py

A ⊗ B := (
    X_A × X_B,           # State space: Cartesian product
    C_A × C_B,           # Admissible: product of admissibles
    (x,y) ↦ V_A(x) + V_B(y)  # Potential: additive
)

# Unit: I = ({*}, {*}, 0)
```

### 2.2 Verification Cost (Regime B)

```python
# src/ck0/cost.py

Δ⁺(f) = max(0, C(x') - C(x))    # Excess violation

verification_cost(f) = base_fee + λ * Δ⁺(f) + penalties
```

Where:
- `C(x)` = CK-0 scalar = ⟨S⁻¹r(x), Σ⁻¹S⁻¹r(x)⟩
- `λ` = global fixed governance stiffness (protocol constant)
- `base_fee` = verification overhead (often 0 for coherent steps)
- `penalties` = policy-specific penalties

### 2.3 Budget Pullback (Grothendieck)

```python
# src/coh/grothendieck.py

def pullback_budget(f: CohMorphism, target_budget: Budget) -> Budget:
    """f*(c) = c + verification_cost(f)"""
    return target_budget + verification_cost(f)

# Morphism exists iff:
# b_prev >= b_next + verification_cost(f)
```

---

## 3️⃣ Implementation Tasks

### Task 1: Add Tensor/Monoidal Structure

**File:** `src/coh/tensor.py` (NEW)

```python
"""
Tensor Product for Coh (Symmetric Monoidal Structure)

A ⊗ B := (X_A × X_B, C_A × C_B, V_A + V_B)
"""

from dataclasses import dataclass
from typing import Callable, Any, Tuple
from .types import CohObject, CohMorphism

def tensor_objects(A: CohObject, B: CohObject) -> CohObject:
    """Form tensor product A ⊗ B with additive potential."""
    # X = X_A × X_B
    def is_state(xy: Tuple[Any, Any]) -> bool:
        x, y = xy
        return A.is_state(x) and B.is_state(y)
    
    # C = C_A × C_B
    def is_admissible(xy: Tuple[Any, Any], eps0: float = 0.0) -> bool:
        x, y = xy
        return A.is_admissible(x, eps0) and B.is_admissible(y, eps0)
    
    # V(x,y) = V_A(x) + V_B(y)
    def potential(xy: Tuple[Any, Any]) -> float:
        x, y = xy
        return A.potential(x) + B.potential(y)
    
    # Δ(ρ_A, ρ_B) = Δ_A(ρ_A) + Δ_B(ρ_B)
    def budget_map(rho: Tuple[Any, Any]) -> float:
        rho_a, rho_b = rho
        return A.budget_map(rho_a) + B.budget_map(rho_b)
    
    # RV: parallel transitions
    def validate(xy1: Tuple, xy2: Tuple, rho: Tuple) -> bool:
        (x1, y1), (x2, y2), (rho_a, rho_b) = xy1, xy2, rho
        return A.validate(x1, x2, rho_a) and B.validate(y1, y2, rho_b)
    
    return CohObject(
        is_state=is_state,
        is_receipt=lambda r: isinstance(r, tuple) and A.is_receipt(r[0]) and B.is_receipt(r[1]),
        potential=potential,
        budget_map=budget_map,
        validate=validate
    )

def tensor_morphisms(f: CohMorphism, g: CohMorphism) -> CohMorphism:
    """Form tensor product of morphisms f ⊗ g."""
    # (f ⊗ g)_X(x, y) = (f_X(x), g_X(y))
    # (f ⊗ g)_♯(ρ_A, ρ_B) = (f_♯(ρ_A), g_♯(ρ_B))
    ...
```

**Status:** ⬜ Pending

---

### Task 2: CK-0 Scalar Canonical Module

**File:** `src/coh/scalar.py` (NEW)

```python
"""
CK-0 Scalar (Coherence Functional)

C(x) = ⟨S⁻¹r(x), Σ⁻¹S⁻¹r(x)⟩

This implements the coherence measurement from CK-0 theory.
"""

from typing import Callable, Any, NamedTuple
from fractions import Fraction

class CK0Scalar(NamedTuple):
    """Canonical coherence scalar."""
    residual: Fraction      # S⁻¹r(x)
    weighted: Fraction      # Σ⁻¹S⁻¹r(x)
    total: Fraction         # ⟨residual, weighted⟩
    
    @property
    def is_admissible(self, eps0: Fraction = Fraction(0)) -> bool:
        return self.total <= eps0


def compute_ck0_scalar(
    state: Any,
    r: Callable[[Any], Any],           # Residual map
    S_inv: Callable[[Any], Any],       # Inverse service map
    Sigma_inv: Callable[[Any], Any]     # Inverse weighting matrix
) -> CK0Scalar:
    """
    Compute C(x) = ⟨S⁻¹r(x), Σ⁻¹S⁻¹r(x)⟩.
    
    Args:
        state: The state x
        r: Residual function r(x)
        S_inv: Inverse service map S⁻¹
        Sigma_inv: Inverse weighting Σ⁻¹
    
    Returns:
        CK0Scalar with residual, weighted, and total components
    """
    # Step 1: r(x)
    residual_raw = r(state)
    
    # Step 2: S⁻¹(r(x))
    service_normalized = S_inv(residual_raw)
    
    # Step 3: Σ⁻¹(S⁻¹(r(x)))
    weighted = Sigma_inv(service_normalized)
    
    # Step 4: Inner product ⟨service_normalized, weighted⟩
    # For scalar case: just multiplication
    total = service_normalized * weighted
    
    return CK0Scalar(
        residual=Fraction(service_normalized),
        weighted=Fraction(weighted),
        total=Fraction(total)
    )


def delta_plus(
    scalar_before: CK0Scalar,
    scalar_after: CK0Scalar
) -> Fraction:
    """
    Compute Δ⁺ = max(0, C(x') - C(x)).
    
    This is the excess violation that triggers governance cost.
    """
    diff = scalar_after.total - scalar_before.total
    return Fraction(max(0, diff))
```

**Status:** ⬜ Pending

---

### Task 3: Governance Cost Module

**File:** `src/ck0/cost.py` (NEW)

```python
"""
Governance Cost Functions

Implements Regime B (bounded violation) cost model:
- verification_cost(f) = base_fee + λ * Δ⁺ + penalties
- Compositional subadditivity: |g ∘ f| ≤ |f| + |g|
"""

from dataclasses import dataclass
from typing import Optional
from fractions import Fraction

# Global governance stiffness (protocol constant)
LAMBDA_GLOBAL: Fraction = Fraction(1)  # Default, configurable


@dataclass(frozen=True)
class CostConfig:
    """Configuration for cost computation."""
    base_fee: Fraction = Fraction(0)
    lambda_global: Fraction = LAMBDA_GLOBAL
    delta_max: Optional[Fraction] = None  # None = unbounded
    penalties: dict = None  # policy_name -> penalty amount
    
    def __post_init__(self):
        if self.penalties is None:
            object.__setattr__(self, 'penalties', {})


def verification_cost(
    delta_plus: Fraction,
    config: CostConfig,
    policy_name: str = "default"
) -> Fraction:
    """
    Compute verification_cost(f) = base_fee + λ * Δ⁺ + penalties.
    
    Args:
        delta_plus: Δ⁺ = max(0, C(x') - C(x))
        config: Cost configuration
        policy_name: Name of policy for penalty lookup
    
    Returns:
        Total authority spent for this transition
    """
    # Check boundedness
    if config.delta_max is not None and delta_plus > config.delta_max:
        raise ValueError(
            f"Violation increase {delta_plus} exceeds policy bound {config.delta_max}"
        )
    
    # Compute cost: base_fee + λ * Δ⁺
    cost = config.base_fee + config.lambda_global * delta_plus
    
    # Add policy penalty if applicable
    penalty = config.penalties.get(policy_name, Fraction(0))
    cost += penalty
    
    return cost


def receipt_cost(receipt) -> Fraction:
    """
    Extract spent budget from a receipt.
    
    This is the canonical value stored in the receipt that
    represents what was actually paid for the transition.
    """
    # Implementation depends on receipt structure
    return receipt.spent_budget


def compositional_cost_bound(
    cost_f: Fraction,
    cost_g: Fraction
) -> Fraction:
    """
    Compute upper bound on composed cost: |g ∘ f| ≤ |f| + |g|.
    
    This is the subadditivity property that makes the oplax
    structure well-defined.
    """
    return cost_f + cost_g


def assert_subadditivity(
    cost_f: Fraction,
    cost_g: Fraction,
    cost_composed: Fraction
) -> bool:
    """
    Assert that |g ∘ f| ≤ |f| + |g|.
    
    Used in tests to verify compositionality guarantees.
    """
    bound = compositional_cost_bound(cost_f, cost_g)
    assert cost_composed <= bound, (
        f"Subadditivity violated: |g∘f|={cost_composed} > |f|+|g|={bound}"
    )
    return True
```

**Status:** ⬜ Pending

---

### Task 4: Budget Pullback (Grothendieck)

**File:** `src/coh/grothendieck.py` (NEW)

```python
"""
Budget Pullback (Grothendieck Construction)

Implements the Grothendieck construction for the oplax fibration:
- f*(c) = c + |f|_V (pullback of budget along morphism)
- Morphism exists iff b_prev >= b_next + |f|_V
"""

from dataclasses import dataclass
from typing import Callable
from fractions import Fraction
from ..ck0.cost import verification_cost, CostConfig
from .types import CohObject, CohMorphism


@dataclass(frozen=True)
class Budget:
    """Budget value in QFixed(18)."""
    value: Fraction
    
    def __add__(self, other: 'Budget') -> 'Budget':
        return Budget(self.value + other.value)
    
    def __ge__(self, other: 'Budget') -> bool:
        return self.value >= other.value


def pullback_budget(
    f: CohMorphism,
    target_budget: Budget,
    cost_config: CostConfig
) -> Budget:
    """
    Compute f*(c) = c + verification_cost(f).
    
    This is the Grothendieck pullback of budget along morphism f.
    
    Args:
        f: The morphism
        target_budget: Current budget c
        cost_config: Cost configuration
    
    Returns:
        Pullback budget f*(c)
    """
    # Compute cost of morphism
    cost = verification_cost(
        delta_plus=f.delta_plus,  # Assumes morphism carries this
        config=cost_config,
        policy_name=f.policy_name
    )
    
    return Budget(target_budget.value + cost)


def morphism_exists(
    f: CohMorphism,
    budget_before: Budget,
    budget_after: Budget,
    cost_config: CostConfig
) -> bool:
    """
    Check if morphism exists under budget constraints.
    
    Morphism f: A → B exists iff:
        b_before >= b_after + |f|_V
    
    This is the budget conservation law from the oplax fibration.
    """
    required = pullback_budget(f, budget_after, cost_config)
    return budget_before >= required
```

**Status:** ⬜ Pending

---

### Task 5: Global vs Instance Morphism Documentation

**File:** `docs/coh/10_morphism_semantics.md` (NEW)

Content should clarify:

- **Global morphism**: Property `V_B(f(x)) ≤ V_A(x) ∀x` - universal quantification
- **Instance morphism certification**: Single executed transition verification
- **Operational Coh_rcpt**: The receipt-discipline variant used in NK-2/NK-4G
- **Distinction**: Verifier checks instance; global is a design-time property

**Status:** ⬜ Pending

---

### Task 6: Categorical Spine Documentation

**File:** `docs/categorical_spine.md` (NEW)

```markdown
# Categorical Spine: Coh–PoC–LoC

## Core Definitions

### Coh Object
A = (X, C, V) where:
- X: State space
- C ⊆ X: Admissible states (V(x) ≤ ε₀)
- V: X → ℝ≥0: Coherence functional

### Coh Morphism
f: A → B satisfies:
- M1: Preserves admissibility
- M2: Covariance of receipts

### Oplax Proof Functor
|f|_V = inf(π) |{ spent V(desc(f), π) = Accept }

### Budget Rule (Grothendieck)
b_next = b_prev - |f|_V
```

**Status:** ⬜ Pending

---

### Task 7: QFixed Determinism Test Suite

**File:** `tests/test_qfixed_determinism.py` (NEW)

```python
"""
Determinism test suite for QFixed(18) arithmetic.

Ensures:
- Cross-platform consistency
- Rounding canonicalization
- Serialization roundtrip
"""

import pytest
from fractions import Fraction

# Simulated QFixed(18) - in practice use actual QFixed implementation
QFixed = Fraction

def test_addition_commutative():
    a = QFixed(1, 10**18)
    b = QFixed(2, 10**18)
    assert a + b == b + a

def test_multiplication_deterministic():
    # Same inputs must always produce same output
    results = []
    for _ in range(100):
        a = QFixed(123456789, 10**18)
        b = QFixed(987654321, 10**18)
        results.append(a * b)
    assert len(set(results)) == 1

def test_serialization_roundtrip():
    # Canonical form must survive serialization
    original = QFixed(123456789012345678, 10**18)
    serialized = str(original.numerator) + '.' + str(original.denominator)
    # ... roundtrip test
    ...
```

**Status:** ⬜ Pending

---

## 4️⃣ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    L1: Coh (Category Theory)                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ types.py    │  │ objects.py  │  │ morphisms.py       │  │
│  │ CohObject   │  │ A1,A2,A3    │  │ M1,M2 verification  │  │
│  │ CohMorphism │  │             │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ limits.py   │  │ tensor.py   │  │ grothendieck.py     │  │
│  │ Product,    │  │ ⊗ (additive)│  │ Budget pullback     │  │
│  │ Pullback    │  │ Symmetric   │  │ f*(c) = c + |f|_V   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌─────────────────────────────────────┐   │
│  │ scalar.py   │  │ cost.py                             │   │
│  │ C(x) =      │  │ verification_cost(f) =              │   │
│  │ ⟨S⁻¹r,Σ⁻¹⟩ │  │ base_fee + λ·Δ⁺ + penalties        │   │
│  └─────────────┘  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    L2: CK-0 (Governance)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ violation.py│  │ budget_law │  │ cost.py (NEW)       │  │
│  │ V(x)        │  │ S(D,B)     │  │ verification_cost() │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              NK Stack (Runtime Implementation)             │
├─────────────────────────────────────────────────────────────┤
│  NK-1 → NK-2 → NK-3 → NK-4G                                 │
│  Policy → Scheduler → Kernel → Verifier                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 5️⃣ Dependency Order

```
Phase 1: Foundation
├── scalar.py (depends on: nothing)
└── cost.py (depends on: scalar.py)

Phase 2: Structural Layer
├── tensor.py (depends on: types.py)
└── grothendieck.py (depends on: cost.py, types.py)

Phase 3: Documentation
├── categorical_spine.md (depends on: all above)
└── 10_morphism_semantics.md (depends on: morphisms.py)

Phase 4: Testing
└── test_qfixed_determinism.py (depends on: cost.py)
```

---

## 6️⃣ Success Criteria

After implementation:

1. ✅ `CohObject` is first-class with explicit V(x) abstraction
2. ✅ CK-0 scalar `C(x)` is computed canonically
3. ✅ `verification_cost(f)` is explicit and deterministic
4. ✅ Budget pullback `f*(c)` is a visible API
5. ✅ Tensor product makes Symmetric Monoidal explicit
6. ✅ Global vs instance morphism distinction is documented
7. ✅ QFixed determinism is tested
8. ✅ Repository reads as "implementation of Coh–PoC–LoC"

---

## 7️⃣ Summary

The hostile audit correctly identified the gap between mathematical theory and code structure. This plan addresses each gap with concrete implementations:

- **Tensor** → Additive, preserving compositionality
- **Cost** → Regime B with global λ for subadditivity
- **Pullback** → Explicit Grothendieck construction
- **Documentation** → Categorical spine formalizing the architecture

The result will be a repository that structurally embodies the categorical theory, not just implements the operations.
