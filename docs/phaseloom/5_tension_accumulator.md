# PhaseLoom Braiding Tension

**Canon Doc Spine v1.0.0** — Section 6

---

## 1. Threading Model

### 1.1 Thread Assignment

Define a deterministic thread assignment function:
k(i) → thread_id

This maps each step i to a thread ID based on:
- Policy label (σ)
- Operation class (solve/repair/resolve)
- Spectral regime label (if present)
- Module ID (NK-3 lowering origin)

### 1.2 Thread Assignment Determinism

The thread assignment must be deterministic:
```python
def thread_assignment(
    step_index: int,
    policy_label: str,
    op_class: OpClass,
    spectral_label: Optional[str],
    module_id: Optional[str]
) -> str:
    """Deterministic thread ID assignment."""
    data = f"{step_index}:{policy_label}:{op_class.value}"
    if spectral_label:
        data += f":{spectral_label}"
    if module_id:
        data += f":{module_id}"
    return sha3_256(data.encode())[:16]  # 16-char thread ID
```

---

## 2. Tension Recurrence

### 2.1 Canonical Formula

T^+ := ρ_T · T + ΔT_inc - ΔT_res

Where:
- (T): Current tension
- (T^+): Next tension
- (ρ_T ∈ [0, 1)): Decay factor
- (ΔT_inc ≥ 0): Tension increment
- (ΔT_res ≥ 0): Tension resolution

### 2.2 Non-negativity

T is always non-negative:
T^+ := max(ρ_T · T + ΔT_inc - ΔT_res, 0)

---

## 3. Tension Increment Sources

### 3.1 Sources of Tension

ΔT_inc may be computed as a fixed-point distance between:

| Source | Description |
|--------|-------------|
| Policy transition | Expected vs observed policy label |
| Budget delta | Expected vs observed budget change |
| Authority delta | Expected vs observed authority change |
| Spectral signature | Expected vs observed spectral changes |

### 3.2 Consensus Options

For v1, two approaches:

**Option A (Off-chain commitment):**
- Compute ΔT_inc, ΔT_res off-chain
- Verify via commitments in receipts
- Risk: Centralization of computation

**Option B (Deterministic on-chain):**
- Define fully deterministic formula
- Recommended for v1

### 3.3 Deterministic Formula (v1 Recommended)

```python
def compute_tension_increment(
    expected_policy: str,
    observed_policy: str,
    expected_budget_delta: FixedPoint,
    observed_budget_delta: FixedPoint,
    expected_authority_delta: FixedPoint,
    observed_authority_delta: FixedPoint
) -> FixedPoint:
    """Compute tension increment deterministically."""
    policy_dist = 0 if expected_policy == observed_policy else FIXED_ONE
    budget_dist = abs(expected_budget_delta - observed_budget_delta)
    auth_dist = abs(expected_authority_delta - observed_authority_delta)
    
    # Weighted sum (weights are governance parameters)
    return policy_dist + budget_dist + auth_dist
```

---

## 4. Tension Resolution

### 4.1 Resolution Sources

ΔT_res comes from explicit resolution actions:

| Action | Description |
|--------|-------------|
| RESOLVE step | Explicit tension reduction |
| Cross-thread sync | Thread alignment |
| Authority injection | Can reset tension |

### 4.2 Resolution Formula

```python
def compute_tension_resolution(
    T: FixedPoint,
    resolution_efficacy: FixedPoint
) -> FixedPoint:
    """Compute tension resolution."""
    return min(T, resolution_efficacy)
```

---

## 5. Threading Model Semantics

### 5.1 Purpose

Tension tracks inconsistency across execution threads:
- Multiple concurrent operations
- Policy transitions
- Budget/authority changes

### 5.2 Interpretation

| Tension Value | Interpretation |
|---------------|----------------|
| (T = 0) | All threads consistent |
| (T > 0) | Cross-thread inconsistency present |
| (T growing) | Divergence increasing |
| (T decreasing) | Convergence occurring |

---

## 6. Receipt Fields

### 6.1 Required Fields

| Field | Description |
|-------|-------------|
| T_prev | Tension before step |
| T_next | Tension after step |
| delta_T_inc | Tension increment |
| delta_T_res | Tension resolution |
| thread_id | Thread assignment |
| policy_label | Current policy |

### 6.2 Verification

The verifier checks:
1. Verify T_next = max(ρ_T * T_prev + delta_T_inc - delta_T_res, 0)
2. Verify delta_T_inc, delta_T_res >= 0

---

## 7. Budget Charge Integration

### 7.1 Tension Cost

Tension increment affects budget through the budget charge law:

Δb ≥ κ_A · A + κ_T · ΔT_inc

Where (κ_T > 0) is the tension budget price.

### 7.2 Cost Implications

- High ΔT_inc → High budget charge
- This disincentivizes policy inconsistency

---

## 8. Implementation Example

### 8.1 Full Update

```python
def update_tension(
    T_prev: FixedPoint,
    delta_T_inc: FixedPoint,
    delta_T_res: FixedPoint,
    rho_T: FixedPoint
) -> FixedPoint:
    """Compute T^+ = rho_T * T + delta_T_inc - delta_T_res"""
    raw = rho_T * T_prev + delta_T_inc - delta_T_res
    return max(raw, FixedPoint(0))
```

### 8.2 Complete Step

```python
def process_step_with_tension(
    state: PLState,
    step: Step,
    params: PLParams
) -> PLState:
    """Process a step and update tension."""
    # Compute increment
    delta_T_inc = compute_tension_increment(
        step.expected_policy,
        step.observed_policy,
        step.expected_budget_delta,
        step.observed_budget_delta,
        step.expected_authority_delta,
        step.observed_authority_delta
    )
    
    # Compute resolution
    delta_T_res = compute_tension_resolution(
        state.T,
        params.resolution_efficacy
    ) if step.op_class == OpClass.RESOLVE else FixedPoint(0)
    
    # Update tension
    T_next = update_tension(
        state.T, delta_T_inc, delta_T_res, params.rho_T
    )
    
    return state.update(T=T_next)
```

---

## 9. Status

- [x] Threading model specified
- [x] Tension recurrence defined
- [x] Increment sources listed
- [x] Resolution mechanism defined
- [ ] Implementation in src/phaseloom/tension.py

---

*The tension accumulator T tracks cross-thread inconsistency, enabling bounds on coherence degradation across parallel execution paths.*
