# CK-0 Invariants

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_state_space.md`](1_state_space.md)

---

## Overview

Invariants are **hard constraints** that must hold for a system to be coherent. Unlike the violation functional `V(x)` (soft constraints), invariant failures are terminal or classified events.

---

## Invariant Definition

An invariant `I` is a predicate:

```
I: X → {true, false}
```

If `I(x) = false`, the system state `x` fails the invariant.

---

## Invariant Categories

| Category | Code | Behavior on Failure |
|----------|------|---------------------|
| Terminal | `INV_TERMINAL` | Abort execution |
| Repairable | `INV_REPAIRABLE` | Trigger repair mode |
| Warning | `INV_WARNING` | Log warning, continue |

---

## Core Invariants

### I1: Debt Non-Negativity

```
I1(x) := (debt(x) ≥ 0)
```

**Category:** Terminal  
**Description:** Debt must never be negative.

---

### I2: Budget Non-Negativity

```
I2(x) := (budget(x) ≥ 0)
```

**Category:** Terminal  
**Description:** Budget must never be negative.

---

### I3: Disturbance Bound Non-Negativity

```
I3(x) := (disturbance(x) ≥ 0)
```

**Category:** Terminal  
**Description:** Disturbance bound must be non-negative.

---

### I4: Step Index Monotonicity

```
I4(x) := (step_index(x) ≥ 0)
```

**Category:** Terminal  
**Description:** Step index must be non-negative.

---

### I5: Debt Upper Bound (Optional)

```
I5(x) := (debt(x) ≤ D_max)
```

Where `D_max` is a declared maximum debt threshold.

**Category:** Terminal or Repairable (implementation-defined)

---

### I6: State Hash Uniqueness

```
I6(x) := (state_hash(x) = H(canonical_encoding(x)))
```

**Category:** Terminal  
**Description:** State hash must match canonical encoding.

---

## Evaluation Order

Invariants must be evaluated in a **deterministic order**:

1. I1 (debt ≥ 0)
2. I2 (budget ≥ 0)
3. I3 (disturbance ≥ 0)
4. I4 (step ≥ 0)
5. I5 (debt ≤ D_max) if defined
6. I6 (hash consistency)

---

## Failure Codes

| Code | Invariant | Description |
|------|-----------|-------------|
| `INV_DEBT_NEG` | I1 | Debt is negative |
| `INV_BUDGET_NEG` | I2 | Budget is negative |
| `INV_DIST_NEG` | I3 | Disturbance is negative |
| `INV_STEP_NEG` | I4 | Step index is negative |
| `INV_DEBT_EXCEEDED` | I5 | Debt exceeds maximum |
| `INV_HASH_MISMATCH` | I6 | State hash does not match |

---

## Contract with Violation Functional

**Critical:** Hard invariant failures are **not** represented by "infinite debt" or any sentinel value inside `V(x)`.

- Invariant failures are handled by the implementation's declared rail policy (REJECT or explicit REPAIR mode)
- If `I(x) = false`, `V(x)` is not evaluated for coherence purposes
- The receipt must record both invariant status and `V(x)` if applicable

---

## Receipt Requirements

Each receipt must include:

- `invariant_status`: pass/fail
- `invariant_failure_code`: code if failed
- `invariant_evaluation_order`: deterministic order used

---

## Extensibility

Additional invariants may be defined:

1. Must have unique identifier
2. Must declare category
3. Must have deterministic evaluation
4. Must produce failure code

---

## Related Documents

- [`3_violation_functional.md`](3_violation_functional.md) - Soft constraints
- [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) - Receipt schema
- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification

---

*Hard invariants are enforced. Failure is terminal or classified.*
