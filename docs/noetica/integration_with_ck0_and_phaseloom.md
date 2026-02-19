# Noetica Integration with CK-0 and PhaseLoom

**Version:** 1.0  
**Status:** Draft  
**Related:** [`0_overview.md`](0_overview.md), [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)

---

## Overview

This document defines the **critical integration points** between Noetica (the language layer) and the underlying modules:

- **CK-0**: Mathematical foundations (violation functional, DebtUnit, curvature)
- **PhaseLoom**: Geometric memory and potential
- **NK**: Runtime governance (gating, verification)

---

## 1. Noetica ↔ CK-0 Integration

### 1.1 solve → V(x) Update

The `solve` construct maps to CK-0's violation functional:

```
Noetica:  solve <budget> state gradients -> state' gradients'
CK-0:     V(x') ≤ V(x) + budget
```

#### Operational Mapping

| Noetica | CK-0 | Description |
|---------|------|-------------|
| `solve` | `MeasuredGate` | Attempt descent |
| Budget | ΔV bound | Maximum V increase allowed |
| State | x ∈ X | CK-0 state space |
| Gradients | ∇V(x) | Violation gradient |

#### Type Correspondence

```
Noetica:  solve <b> s g -> s' g'
CK-0:     Gate(x, b) → (x', receipt)
           where x' = argmin V(y) subject to V(y) ≤ V(x) + b
```

### 1.2 repair → Curvature Restoration

The `repair` construct maps to PhaseLoom curvature accumulator:

```
Noetica:  repair <budget> state gradients -> state' gradients'
PhaseLoom: C' = decay(C, budget)
```

#### Operational Mapping

| Noetica | CK-0/PhaseLoom | Description |
|---------|----------------|-------------|
| `repair` | Curvature update | Reduce curvature bound |
| Budget | Curvature decay | Amount to reduce C |
| Gradients | Curvature C | Curvature accumulator |

### 1.3 measure → V(x) Reading

The `measure` construct reads the CK-0 violation functional:

```
Noetica:  measure state -> measurement
CK-0:     V(x) → DebtUnit
```

#### Operational Mapping

| Noetica | CK-0 | Description |
|---------|------|-------------|
| `measure` | ViolationFunctional.compute | Compute V(x) |
| State | x | CK-0 state |
| Measurement | DebtUnit | Exact V(x) value |

### 1.4 DebtUnit Integration

All quantitative values in Noetica use CK-0's DebtUnit:

```
Budget        → DebtUnit (exact integer)
Measurement   → DebtUnit (exact integer)
Threshold     → DebtUnit (exact integer)
Scale         → Fixed at 1000 (from canonical_profile)
```

---

## 2. Noetica ↔ PhaseLoom Integration

### 2.1 freeze → Interlock Activation

The `freeze` construct activates PhaseLoom interlock:

```
Noetica:  freeze loom_state frozen_state -> locked_budget
PhaseLoom: activate_interlock(PLState)
```

#### PhaseLoom State Transition

```
Before freeze:
  PLState = (loom, frozen, phase=Loom)

After freeze:
  PLState = (loom⊥, frozen', phase=Frozen)
  Interlock: active = true
```

### 2.2 thaw → Interlock Release

The `thaw` construct releases PhaseLoom interlock:

```
Noetica:  thaw locked_budget -> budget
PhaseLoom: deactivate_interlock(PLState)
```

#### PhaseLoom State Transition

```
Before thaw:
  PLState = (loom⊥, frozen, phase=Frozen)
  Interlock: active = true

After thaw:
  PLState = (loom', frozen⊥, phase=Loom)
  Interlock: active = false
```

### 2.3 solve/repair → Potential Update

The geometric operations update PhaseLoom's potential:

```
V_PL(s') = V_PL(s) - γ · T
```

Where:
- V_PL: PhaseLoom Potential
- γ: Learning rate (fixed)
- T: Tension accumulator

---

## 3. Noetica ↔ NK Integration

### 3.1 mint/burn → NK-1 Gate

The mint and burn constructs interact with NK-1's gating:

```
mint:   Requires ServiceLaw.gate = pass
burn:   Requires ServiceLaw.gate = pass
```

### 3.2 emit → Receipt Chain

The `emit_checkpoint` construct produces NK-4G-verifiable receipts:

```
Noetica:  emit -> checkpoint_receipt
NK-4G:    Verify(receipt) → pass/fail
```

#### Receipt Structure

```json
{
  "type": "checkpoint",
  "version": "noetica_v1",
  "state_hash": "sha256(state)",
  "v_x": "DebtUnit",
  "phase": "Loom|Frozen",
  "curvature": "DebtUnit",
  "tension": "DebtUnit",
  "receipt_chain": ["prev_hash_1", "prev_hash_2"]
}
```

### 3.3 Program → NK-2 → NK-3

Noetica programs compile through NK:

```
Noetica source
    ↓ (lower)
NK-3: NSC → OpSet → DAG
    ↓
NK-2: ExecPlan → Scheduler
    ↓
NK-1: Gate → Execution → Receipt
```

---

## 4. Verification Pipeline

### 4.1 Compile-Time Verification

1. **Type checking**: Linear types, phase rules
2. **Refinement proof**: QF-LRA-FP predicates
3. **Budget analysis**: Sufficient budget for operations

### 4.2 Runtime Verification (STF)

1. **Gate check**: NK-1 MeasuredGate passes
2. **Budget check**: Budget remains positive
3. **Phase check**: Correct phase for operation
4. **Receipt check**: Hash chain valid

### 4.3 Post-Execution Verification

1. **NK-4G**: Receipt verification
2. **ASG**: Spectral certificate validation
3. **Curvature check**: C bound maintained

---

## 5. State Correspondence

### Noetica State to CK-0/PhaseLoom

```
Noetica State:
  - budget: DebtUnit
  - loom_state: PLState
  - frozen_state: State
  - phase: Phase
  - receipts: [Receipt]

CK-0 State:
  - x ∈ X (state space)
  
PhaseLoom State:
  - PLState = (loom, frozen, C, T, phase)
```

### State Transition Rules

| Noetica Op | CK-0 | PhaseLoom | NK-1 |
|------------|------|-----------|------|
| mint | - | - | Gate check |
| burn | - | - | Gate check |
| solve | V(x') ≤ V(x)+b | V_PL update | Gate check |
| repair | V update | C decay | Gate check |
| freeze | - | Interlock on | - |
| thaw | - | Interlock off | - |
| measure | V(x) read | V_PL read | - |
| emit | - | - | Receipt |

---

## 6. Reference Tables

### Construct → Module Mapping

| Construct | Primary Module | Secondary Module |
|-----------|----------------|------------------|
| mint | NK-1 | - |
| burn | NK-1 | - |
| solve | CK-0 | PhaseLoom |
| repair | PhaseLoom | CK-0 |
| freeze | PhaseLoom | - |
| thaw | PhaseLoom | - |
| measure | CK-0 | PhaseLoom |
| emit | NK-4G | - |

### Type → Module Mapping

| Type | Module |
|------|--------|
| DebtUnit | CK-0 |
| ViolationFunctional | CK-0 |
| CurvatureMatrix | CK-0 |
| PLState | PhaseLoom |
| V_PL | PhaseLoom |
| Receipt | NK-4G |

---

## 7. References

- Overview: [`0_overview.md`](0_overview.md)
- Kernel spec: [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)
- CK-0: [`../ck0/0_overview.md`](../ck0/0_overview.md)
- PhaseLoom: [`../phaseloom/0_overview.md`](../phaseloom/0_overview.md)
- NK-1: [`../nk1/0_overview.md`](../nk1/0_overview.md)
- NK-4G: [`../nk4g/0_overview.md`](../nk4g/0_overview.md)
