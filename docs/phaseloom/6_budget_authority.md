# PhaseLoom Budget and Authority Laws

**Canon Doc Spine v1.0.0** — Section 7

---

## 1. Budget Update Law

### 1.1 Canonical Formula

b^+ := b - Δb

Where:
- (b): Current budget
- (b^+): Next budget
- (Δb ≥ 0): Budget expenditure

### 1.2 Constraints

- Budget is non-negative: b ∈ ℝ_≥0
- Expenditure is non-negative: Δb ≥ 0
- Cannot spend more than available: Δb ≤ b

### 1.3 Implementation

```python
def update_budget(b: FixedPoint, delta_b: FixedPoint) -> FixedPoint:
    """Compute b^+ = b - delta_b"""
    if delta_b > b:
        raise BudgetExhaustedError("Insufficient budget")
    return b - delta_b
```

---

## 2. Authority Update Law

### 2.1 Canonical Formula

a^+ := a + Δa

Where:
- (a): Current authority
- (a^+): Next authority
- (Δa ≥ 0): Authority injection

### 2.2 Constraints

- Authority is non-negative: a ∈ ℝ_≥0
- Injection is non-negative: Δa ≥ 0
- Authority only increases (no withdrawal in v1)

### 2.3 Implementation

```python
def update_authority(a: FixedPoint, delta_a: FixedPoint) -> FixedPoint:
    """Compute a^+ = a + delta_a"""
    if delta_a < FixedPoint(0):
        raise InvalidAuthorityDeltaError("Authority cannot decrease")
    return a + delta_a
```

---

## 3. Budget Charge Law

### 3.1 Contract Statement

For all accepted transitions:

Δb ≥ κ_A · A + κ_T · ΔT_inc

Where:
- (κ_A > 0): Amplification budget price
- (κ_T > 0): Tension increment budget price
- (A): Amplification (Δv)_+
- (ΔT_inc): Tension increment

### 3.2 Interpretation

This is the "risk costs budget" axiom:
- Every unit of amplification costs κ_A budget
- Every unit of tension increment costs κ_T budget
- Budget is the governance resource that limits risky exploration

### 3.3 Verification

```python
def verify_budget_charge(
    delta_b: FixedPoint,
    A: FixedPoint,
    delta_T_inc: FixedPoint,
    kappa_A: FixedPoint,
    kappa_T: FixedPoint
) -> bool:
    """Verify budget charge law."""
    required = kappa_A * A + kappa_T * delta_T_inc
    return delta_b >= required
```

### 3.4 Status

**[CONTRACT]** - Enforced by STF (State Transition Function)

---

## 4. Cost Parameters

### 4.1 Parameter Definitions

| Parameter | Type | Description |
|-----------|------|-------------|
| κ_A | FixedPoint > 0 | Amplification price |
| κ_T | FixedPoint > 0 | Tension increment price |
| b_min | FixedPoint ≥ 0 | Interlock floor |
| b_init | FixedPoint > 0 | Initial budget |

### 4.2 Governance

These parameters are governance-controlled:
- Set by DAO/policy bundle
- Cannot change during execution epoch
- Part of parameter bundle (see Section 13)

---

## 5. Budget Flow

### 5.1 Sources of Budget

| Source | Description |
|--------|-------------|
| Initial allocation | b_init at genesis |
| Authority injection | Δb_inj > 0 with AUTH_INJECT |
| Reward | Optional reward for V reduction |

### 5.2 Sinks of Budget

| Sink | Description |
|------|-------------|
| Amplification | κ_A · A |
| Tension increment | κ_T · ΔT_inc |
| Computation cost | Fixed per-step cost |

---

## 6. Authority Injection

### 6.1 Relationship to Budget

Authority injection can increase budget:
- AUTH_INJECT step: b^+ > b, a^+ > a
- This is the only way to increase budget

### 6.2 Budget Increase

```python
def apply_authority_injection(
    b: FixedPoint,
    a: FixedPoint,
    delta_b_inj: FixedPoint,
    delta_a_inj: FixedPoint
) -> Tuple[FixedPoint, FixedPoint]:
    """Apply authority injection."""
    if delta_b_inj <= FixedPoint(0) or delta_a_inj <= FixedPoint(0):
        raise InvalidInjectionError("Injection must be positive")
    return (b + delta_b_inj, a + delta_a_inj)
```

---

## 7. Interlock Interaction

### 7.1 Budget Floor

When b ≤ b_min:
- SOLVE steps with A > 0 are rejected
- Only REPAIR, RESOLVE, AUTH_INJECT allowed

### 7.2 Complete Interlock Rule

See Section 8 (docs/phaseloom/8_interlock.md) for full interlock definition.

---

## 8. Receipt Fields

### 8.1 Required Fields

| Field | Description |
|-------|-------------|
| b_prev | Budget before step |
| b_next | Budget after step |
| a_prev | Authority before step |
| a_next | Authority after step |
| delta_b | Budget expenditure |
| delta_a | Authority injection |

### 8.2 Verification

The verifier checks:
1. b_next = b_prev - delta_b
2. a_next = a_prev + delta_a
3. delta_b >= κ_A · A + κ_T · ΔT_inc
4. If AUTH_INJECT: multisig verification

---

## 9. Example Trace

### 9.1 Sample Execution

| Step | Type | v→v^+ | A | D | ΔT_inc | Δb (required) | b |
|------|------|-------|---|---|--------|---------------|---|
| 0 | - | - | - | - | - | - | 1000 |
| 1 | SOLVE | 1.0→0.8 | 0 | 0.2 | 0 | 0 | 1000 |
| 2 | SOLVE | 0.8→1.2 | 0.4 | 0 | 0 | 0.4·κ_A | 1000-0.4·κ_A |
| 3 | SOLVE | 1.2→1.6 | 0.4 | 0 | 0.1 | 0.4·κ_A+0.1·κ_T | ... |
| 4 | AUTH_INJECT | 1.6→1.6 | 0 | 0 | 0 | -100 | b+100 |

---

## 10. Status

- [x] Budget update law specified
- [x] Authority update law specified
- [x] Budget charge law (contract) defined
- [x] Interlock interaction defined
- [ ] Implementation in src/phaseloom/

---

*The budget and authority laws provide the governance coupling to the geometric dynamics. The budget charge law is a hard contract enforced by the STF.*
