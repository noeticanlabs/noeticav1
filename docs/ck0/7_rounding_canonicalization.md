# CK-0 Rounding and Canonicalization

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`B_reference_constants.md`](B_reference_constants.md)

---

## Overview

This document defines the **anti-wedgeability** discipline: the canonical rules for rounding, rational reduction, and numeric representation. If someone changes these rules, they break replay.

---

## Canonical Number Representation

### Integers
- Use base `CK0_INT_BASE = 10`
- No leading zeros (except "0")
- Use minimum number of digits

### Rationals
- **Must reduce to lowest terms**
- Store as `(numerator, denominator)` with `gcd(|num|, den) = 1`
- Denominator > 0

---

## Rounding Mode

| Constant | Value |
|----------|-------|
| `CK0_ROUNDING_MODE` | `half_even` (banker's rounding) |

### Half-Even Rules

| Input | Result |
|-------|--------|
| 2.5 | 2 (even) |
| 3.5 | 4 (even) |
| 1.5 | 2 (even) |
| 0.5 | 0 (even) |

---

## Scaling Policies

### DebtUnit Scaling

| Constant | Value |
|----------|-------|
| `CK0_DEBT_UNIT_SCALE` | 1 (no scaling) |
| `CK0_DEBT_UNIT_TYPE` | integer |

All debt values are **integers**. No floating-point debt in receipts.

### BudgetUnit Scaling

| Constant | Value |
|----------|-------|
| `CK0_BUDGET_UNIT_SCALE` | 1 |

---

## LCM Handling

When combining fractions:

1. Compute LCM of denominators
2. Scale numerators
3. Reduce result to lowest terms

Example:
```
1/3 + 1/6 = 2/6 + 1/6 = 3/6 = 1/2
```

---

## Comparison Rules

All comparisons in CK-0 use **exact rational arithmetic**:

```
a < b  ⇔  a·den_b < b·den_a  (with denominators positive)
```

No tolerance-based comparisons. No epsilon.

---

## Hash Input Bytes

When computing hashes, numbers must be encoded canonically:

### Integer Encoding
```
"123"  (ASCII decimal, no leading zeros)
```

### Rational Encoding
```
"num/den"  (reduced form, no spaces)
```

### Floating-Point (DISALLOWED in authoritative computation)

CK-0 does **not** allow floating-point for:
- Debt values in receipts
- Violation functional values in gating
- Budget law verification

Floating-point may be used internally for performance, but must be converted to integers before authoritative computation.

---

## Canonical JSON Field Order

Fields in JSON objects must be in **lexicographic order**:

```json
{
  "action_hash": "abc123",
  "budget": 100,
  "debt_after": 5,
  "debt_before": 10,
  "disturbance": 0,
  "invariant_status": "pass",
  "state_after": "def456",
  "state_before": "ghi789",
  "step_index": 42,
  "V_policy_id": "CK0.v1",
  "V_total": 3
}
```

---

## Anti-Wedgeability

**Wedgeable:** A representation that can be parsed multiple ways.

**CK-0 Anti-Wedgeability Rules:**

| Rule | Description |
|------|-------------|
| Unique representation | Every value has exactly one canonical encoding |
| No whitespace variations | Canonical JSON has no extra whitespace |
| No equivalent forms | "1/2" not "2/4", "1.0" not "1" |
| Sorted keys | Object keys always sorted |

---

## Breaking Change Detection

If canonicalization rules change:

1. Receipts from old rules cannot be verified
2. Version must be bumped
3. Migration path required

---

## Receipt Requirements

Each receipt must include:

| Field | Type | Description |
|-------|------|-------------|
| `canonicalization_version` | String | CK0 canonicalization version |
| `rounding_mode` | String | e.g., "half_even" |
| `hash_input_encoding` | String | How numbers encoded in hash |

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ Canonical: unique representation, half-even rounding,    │
│            reduced rationals, sorted keys, no floats      │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`3_violation_functional.md`](3_violation_functional.md) - V computation
- [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) - Receipt schema
- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification

---

*No wedgeable to parse. One truth, one encoding.*
