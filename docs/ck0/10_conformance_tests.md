# CK-0 Conformance Tests

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`9_replay_verifier.md`](9_replay_verifier.md)

---

## Overview

Conformance tests ensure CK-0 implementations are **enforceable** rather than just documented. This document defines test vectors and acceptance criteria.

---

## Test Categories

### T1: Golden Vector Tests
Exact byte-level verification of canonical encodings.

### T2: Gate Accept/Reject Cases
Verify correct decision making for coherent/incoherent states.

### T3: Rounding Edge Cases
Canonical rounding behavior verification.

### T4: Replay Over N Steps
Multi-step verification with matching hashes.

### T5: Negative Tests
Cases that MUST fail.

---

## T1: Golden Vector Tests

### Test T1.1: Minimal State

**Input:**
```json
{
  "debt": 0,
  "budget": 0,
  "disturbance": 0,
  "step_index": 0,
  "receipt_chain_hash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

**Expected canonical encoding bytes:** `[...]`  
**Expected hash:** `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### Test T1.2: Non-Zero Debt

**Input:**
```json
{
  "debt": 100,
  "budget": 50,
  "disturbance": 10,
  "step_index": 1,
  "receipt_chain_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

**Expected:** Canonical JSON with sorted keys

### Test T1.3: Rational Reduction

**Input:** Violation functional with `r = 2/4, σ = 1`

**Expected:** Normalized to `r = 1/2`

---

## T2: Gate Accept/Reject Cases

### Test T2.1: Accept - Coherent State

| Field | Value |
|-------|-------|
| debt_before | 10 |
| budget | 100 |
| disturbance | 0 |
| service | min(10, 1.0·100) = 10 |
| debt_after | 0 |

**Budget law:** `0 ≤ 10 - 10 + 0` → **ACCEPT**

### Test T2.2: Accept - With Disturbance

| Field | Value |
|-------|-------|
| debt_before | 10 |
| budget | 5 |
| disturbance | 3 |
| service | min(10, 1.0·5) = 5 |
| debt_after | 8 |

**Budget law:** `8 ≤ 10 - 5 + 3 = 8` → **ACCEPT**

### Test T2.3: Reject - Law Violation

| Field | Value |
|-------|-------|
| debt_before | 10 |
| budget | 5 |
| disturbance | 0 |
| debt_after | 8 |

**Budget law:** `8 ≤ 10 - 5 + 0 = 5` → **FALSE** → **REJECT**

### Test T2.4: Reject - Negative Debt

| Field | Value |
|-------|-------|
| debt_before | 5 |
| budget | 10 |
| debt_after | -1 |

**Invariant failure:** `debt_after < 0` → **REJECT**

---

## T3: Rounding Edge Cases

### Test T3.1: Half-Even Rounding

| Input | Expected |
|-------|----------|
| 2.5 | 2 |
| 3.5 | 4 |
| 1.5 | 2 |
| 0.5 | 0 |
| -0.5 | 0 |
| -1.5 | -2 |

### Test T3.2: Rational Reduction

| Input | Expected |
|-------|----------|
| 2/4 | 1/2 |
| 3/6 | 1/2 |
| 4/8 | 1/2 |
| 10/100 | 1/10 |

### Test T3.3: Zero Denominator (MUST FAIL)

| Input | Expected |
|-------|----------|
| 1/0 | INVALID |

---

## T4: Replay Over N Steps

### Test T4.1: 3-Step Replay

**Step 0 → 1:**
- debt: 10 → 5 (service: 5, budget: 10)
- receipt_hash_0 → receipt_hash_1

**Step 1 → 2:**
- debt: 5 → 2 (service: 3, budget: 5, disturbance: 0)
- receipt_hash_1 → receipt_hash_2

**Step 2 → 3:**
- debt: 2 → 0 (service: 2, budget: 5)
- receipt_hash_2 → receipt_hash_3

**Verification:** Hash chain must match at each step.

### Test T4.2: Disturbance Accumulation

**Step:**
- debt: 0
- disturbance: 5
- debt_after: 5 (law: 5 ≤ 0 - 0 + 5)

**Verification:** Correct accounting of disturbance.

---

## T5: Negative Tests (MUST FAIL)

### Test T5.1: Negative Budget

```
debt_before: 10, budget: -5, disturbance: 0
```

**Expected:** Invariant failure (I2: budget ≥ 0)

### Test T5.2: Negative Disturbance

```
debt_before: 10, budget: 0, disturbance: -3
```

**Expected:** Invariant failure (I3: disturbance ≥ 0)

### Test T5.3: Debt Exceeds Maximum

```
D_max: 100
debt_before: 101
```

**Expected:** Invariant failure (I5: debt ≤ D_max)

### Test T5.4: Hash Chain Break

```
receipt[i].prev_receipt_hash != receipt[i-1].receipt_hash
```

**Expected:** VFY_HASH_CHAIN_BROKEN

### Test T5.5: V Mismatch

```
computed V(x) != receipt.debt_before
```

**Expected:** VFY_V_MISMATCH

---

## Test Vectors Format

Each test includes:

```json
{
  "test_id": "T2.1",
  "description": "Accept - coherent state",
  "input": { ... },
  "expected": {
    "gate_decision": "accept",
    "law_satisfied": true,
    "verification_result": "valid"
  }
}
```

---

## Running Tests

CK-0 implementations MUST pass:

1. All golden vector tests (exact bytes)
2. All gate accept/reject cases
3. All rounding edge cases
4. All N-step replay tests
5. All negative tests (correct failure)

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ Conformance: Pass all test vectors or fail - no wiggle    │
│             room for "mostly compliant" implementations   │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification algorithm
- [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) - Rounding rules
- [`4_budget_debt_law.md`](4_budget_debt_law.md) - Budget law

---

*CK-0 is enforceable. These tests prove it.*
