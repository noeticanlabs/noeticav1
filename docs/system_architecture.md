# Noetica System Architecture

## Overview

The Noetica system implements a layered architecture for coherent computation, starting from mathematical foundations (Coh) through runtime implementations (NK-1/2/3).

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    L1: Mathematical Foundation               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Coh (Category Theory)                  │  │
│  │    Objects: (X, V, RV)  |  Morphisms preserve RV     │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           CK-0 (Full Subcategory of Coh)              │  │
│  │    V(x) = r̃(x)ᵀW r̃(x)  |  Budget/ Debt Laws     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  L2: Operational Calculus                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              NEC (Noetica Execution Calculus)          │  │
│  │    Batching, Gate Law, Split Law, Receipts           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    L3: Runtime Implementation               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   NK-1      │→ │   NK-2      │→ │   NK-3      │       │
│  │  Verifier   │  │  Scheduler  │  │   Kernel    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    L4: Extensions                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   NK-4G     │  │  PhaseLoom  │  │    ASG      │       │
│  │  Governance  │  │    Memory   │  │  Spectral   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Dependency Graph

### Coh (L1 - Mathematical Foundation)

```
src/coh/
├── __init__.py        # Public API exports
├── types.py           # CohObject, CohMorphism definitions
├── objects.py         # Axiom verification (A1, A2, A3)
├── morphisms.py       # Morphism preservation (M1, M2)
├── category.py        # Identity, composition, products
├── functors.py       # Time functors F: ℕ → Coh
├── limits.py         # Products, pullbacks
├── ck0_integration.py # CK-0 subcategory
└── functors_builtin.py # Built-in functors (Vio, Adm, Transition)
```

**Purpose:** Defines the mathematical category of coherent spaces with:
- **Objects**: (X, V, RV) - state space, potential, validator
- **Morphisms**: State maps + receipt maps preserving validity
- **Category Laws**: Identity, composition, products

### CK-0 (L1 - Semantic Instance)

```
src/ck0/
├── __init__.py
├── constants.py       # Reference constants (B_ref, etc.)
├── state_space.py     # Typed state definitions
├── invariants.py     # Hard invariants I(x)
├── violation.py      # V(x) = r̃(x)ᵀW r̃(x)
├── budget_debt_law.py # Service law: D' ≤ D - S(D,B) + E
├── curvature.py       # NEC closure analysis
└── ...
```

**Purpose:** Concrete instance of Coh with:
- Weighted residual norm potential
- Budget/debt accounting
- Service laws

### NEC (L2 - Operational Calculus)

```
src/nec/
├── __init__.py
├── state_space.py    # NEC state definitions
├── contract_structure.py # Delta contracts
├── delta_norms.py   # Norm computations
├── gate_law.py      # Batch aggregation
├── split_law.py     # Failure handling
└── ...
```

**Purpose:** Operational layer defining:
- Deterministic batching
- Gate/split laws
- Receipt witnesses

### NK-1 (L3 - Verifier)

```
src/nk1/
├── __init__.py
├── curvature_matrix.py # Curvature computations
├── measured_gate.py   # Gate measurements
├── policy_bundle.py  # Policy management
├── receipt_canon.py # Receipt canonicalization
├── state_canon.py   # State canonicalization
└── ...
```

**Purpose:** Runtime verifier implementing:
- Receipt validation
- Policy enforcement
- State canonicalization

### NK-2 (L3 - Scheduler)

```
src/nk2/
├── __init__.py
├── exec_plan.py     # Execution planning
├── scheduler.py     # Task scheduling
├── failure_handling.py # Failure recovery
└── ...
```

**Purpose:** Runtime scheduler for:
- Batch execution
- Resource allocation
- Failure handling

### NK-3 (L3 - Kernel)

```
src/nk3/
├── __init__.py
├── canon_inputs.py  # Input canonicalization
├── dag.py           # DAG operations
├── opset.py         # Operation registry
└── ...
```

**Purpose:** Kernel-level execution:
- DAG scheduling
- Operation execution
- Module receipts

### NK-4G (L4 - Governance)

```
src/nk4g/
├── __init__.py
├── policy.py        # Policy definitions
├── receipt_fields.py # Governance receipts
└── verifier.py      # Governance verifier
```

**Purpose:** Extended governance:
- Policy enforcement
- Metric tracking
- Spectral analysis integration

### PhaseLoom (L4 - Geometric Memory)

```
src/phaseloom/
├── __init__.py
├── curvature.py     # Curvature accumulator
├── tension.py       # Tension accumulator
├── authority.py     # Authority injection
├── potential.py     # Extended Lyapunov
├── interlock.py     # Budget interlock
├── receipt.py       # PhaseLoom receipts
└── verifier.py      # PhaseLoom verifier
```

**Purpose:** Geometric memory extension:
- State augmentation with (C, T, B, A)
- Extended potential V_PL
- Descent guarantees

### ASG (L4 - Spectral)

```
src/asg/
├── __init__.py
├── assembly.py      # ASG assembly
├── digest.py        # Operator digests
├── operators.py     # ASG operators
├── spectral.py      # Spectral analysis
├── types.py         # ASG types
└── watchdog.py      # Watchdog receipts
```

**Purpose:** Spectral analysis:
- Operator decomposition
- Watchdog tracking
- Kappa computation

---

## Data Flow

### 1. Definition Phase (Design Time)

```
User defines:
  → CK-0 Contract (V, invariants, service law)
  → NEC Operations (batching, gate, split)
  → NK Policies
```

### 2. Compilation Phase (Build Time)

```
CK-0 Contract
    ↓
NEC Operations (compile to DAG)
    ↓
NK-1 Verifier (generate validate function)
    ↓
NK-2 Scheduler (generate exec plan)
    ↓
NK-3 Kernel (generate module receipts)
```

### 3. Execution Phase (Runtime)

```
User Input
    ↓
NK-3 Kernel (execute DAG)
    ↓
NK-2 Scheduler (manage batches)
    ↓
NK-1 Verifier (validate receipts)
    ↓
PhaseLoom (update geometric memory)
    ↓
ASG (track spectral properties)
    ↓
NK-4G (governance enforcement)
```

### 4. Verification Phase (Post-Execution)

```
Execution Trace
    ↓
Receipt Chain (verify determinism)
    ↓
Coh Axioms (verify A1, A2, A3)
    ↓
CK-0 Laws (verify budget/debt)
    ↓
NEC Closure (verify curvature bounds)
```

---

## Key Interfaces

### Coh Object Interface

```python
class CohObject:
    is_state(x: Any) -> bool           # X membership
    is_receipt(r: Any) -> bool        # Rec membership  
    potential(x: Any) -> float         # V: X → ℝ≥0
    budget_map(r: Any) -> float        # Δ: Rec → ℝ≥0
    validate(x, y, r) -> bool         # RV(x, y, r)
```

### CK-0 Receipt Interface

```python
class CK0Receipt:
    policy_id: str
    budget: DebtUnit
    debt: DebtUnit
    residual: List[float]
    hash: str
    timestamp: int
```

### PhaseLoom State Interface

```python
class PhaseLoomState:
    x: Any           # Base state
    C: float         # Curvature (clamped ≥ 0)
    T: float         # Tension
    B: float         # Budget
    A: float         # Authority
```

---

## Test Organization

```
tests/
├── test_coh.py              # Coh axioms (19 tests)
├── test_budget_law.py      # CK-0 service laws
├── test_debtunit.py        # DebtUnit arithmetic
├── test_delta_norm.py      # Norm computations
├── test_curvature.py       # Curvature analysis
├── test_batch_epsilon.py   # Batch epsilon
└── ...
```

---

## Conformance

Golden vectors for verification:

```
conformance/
├── receipt_canon.json      # Receipt canonicalization
├── state_canon.json       # State canonicalization
├── debtunit_golden.json   # DebtUnit operations
├── policy_golden.json     # Policy definitions
├── service_law_golden.json # Service law outputs
└── ...
```

---

## Summary

The Noetica system works as follows:

1. **Coh** provides the mathematical foundation (category theory)
2. **CK-0** instantiates Coh with weighted residuals and budget/debt
3. **NEC** defines operational semantics (batching, gates)
4. **NK-1/2/3** implement the runtime (verify, schedule, execute)
5. **PhaseLoom** extends state with geometric memory
6. **NK-4G** and **ASG** provide governance and analysis

All layers preserve the core invariant: **deterministic, receipt-verified transitions** that compose mathematically.
