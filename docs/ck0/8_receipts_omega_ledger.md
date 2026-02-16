# CK-0 Receipts (Ω-Ledger)

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_state_space.md`](1_state_space.md)

---

## Overview

A **receipt** is an immutable record of a single step's execution. Receipts form a hash chain (the Ω-ledger) that enables replay verification.

---

## Receipt Schema

```json
{
  "receipt_version": 1,
  "receipt_id": "uuid-v4",
  "step_index": 42,
  "timestamp": "2026-02-16T00:00:00Z",
  
  "state_before": "abc123...",
  "state_after": "def456...",
  "action_hash": "ghi789...",
  "prev_receipt_hash": "jkl012...",
  
  "debt_before": 10,
  "debt_after": 5,
  "budget": 100,
  "disturbance": 0,
  "service_applied": 5,
  "service_policy_id": "CK0.service.v1",
  "service_instance_id": "linear_capped.mu:1.0",
  "law_satisfied": true,
  
  "V_policy_id": "CK0.v1",
  "V_total": 3,
  "contract_set_id": "contract_hash...",
  "active_contract_bitmap": "0b1011",
  
  "invariant_status": "pass",
  "invariant_failure_code": null,
  
  "gate_decision": "accept",
  "gate_reason": "coherence_satisfied",
  
  "canonicalization_version": "1.0",
  "rounding_mode": "half_even",
  
  "receipt_signature": "optional_signature..."
}
```

---

## Required Fields

### Chain Fields

| Field | Type | Description |
|-------|------|-------------|
| `receipt_id` | UUID | Unique receipt identifier |
| `step_index` | Natural | Step number |
| `prev_receipt_hash` | Hash | Hash of previous receipt (or null for genesis) |
| `receipt_hash` | Hash | Hash of this receipt |

### State Fields

| Field | Type | Description |
|-------|------|-------------|
| `state_before` | Hash | State hash before transition |
| `state_after` | Hash | State hash after transition |
| `action_hash` | Hash | Action descriptor hash |

### Budget/Debt Fields

| Field | Type | Description |
|-------|------|-------------|
| `debt_before` | DebtUnit | `D_k` |
| `debt_after` | DebtUnit | `D_{k+1}` |
| `budget` | BudgetUnit | `B_k` |
| `disturbance` | DisturbanceUnit | `E_k` |
| `service_applied` | DebtUnit | `S(D_k, B_k)` |
| `service_policy_id` | String | Policy ID (e.g., "CK0.service.v1") |
| `service_instance_id` | String | Instance ID (e.g., "linear_capped.mu:1.0") |
| `law_satisfied` | Boolean | Whether budget law holds |

### Violation Functional Fields

| Field | Type | Description |
|-------|------|-------------|
| `V_policy_id` | String | Policy used (e.g., "CK0.v1") |
| `V_total` | DebtUnit | Total violation |
| `contract_set_id` | Hash | Contract set identifier |
| `active_contract_bitmap` | Bitfield | Active contract indicators |

### Invariant Fields

| Field | Type | Description |
|-------|------|-------------|
| `invariant_status` | String | "pass" or "fail" |
| `invariant_failure_code` | String | Code if failed |

### Gate Fields

| Field | Type | Description |
|-------|------|-------------|
| `gate_decision` | String | "accept", "reject", "repair" |
| `gate_reason` | String | Human-readable reason |

---

## Canonical JSON Field Order

Fields **must** be in lexicographic order:

```
action_hash, budget, contract_set_id, debt_after, debt_before, 
disturbance, gate_decision, gate_reason, invariant_failure_code, 
invariant_status, prev_receipt_hash, receipt_hash, receipt_id, 
receipt_signature, receipt_version, rounding_mode, service_applied, 
service_instance_id, service_policy_id, state_after, state_before, 
step_index, timestamp, V_policy_id, V_total
```

---

## Hash Chain

### Genesis Receipt
```
prev_receipt_hash = null
receipt_hash = H(receipt_content)
```

### Subsequent Receipts
```
prev_receipt_hash = H(previous_receipt)
receipt_hash = H(receipt_content)
```

### Hash Input

The hash input includes all fields **except** `receipt_hash` and `receipt_signature`.

---

## Canonical Hashing Input

When computing hashes:

1. Encode receipt as canonical JSON
2. Use SHA3_256 (or configured algorithm)
3. Output as lowercase hex string

---

## Signature Options

Receipt signatures are **optional** at CK-0 level:

- Unsigned receipts are valid for replay
- Signatures may be added for non-repudiation
- Signature scheme is implementation-defined

---

## Per-Contract Receipt Data

For each active contract, include:

| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | String | Contract identifier |
| `m_k` | Natural | Residual dimension |
| `sigma_spec_id` | String | Normalizer spec |
| `weight_spec_id` | String | Weight spec |
| `r2` | DebtUnit | `||r̃_k||₂²` (required) |
| `r_inf` | DebtUnit | `||r̃_k||_∞` (optional) |
| `r_hash` | Hash | Commitment (optional) |

---

## Storage

Receipts are stored in the Ω-ledger:

```
Ω = [receipt_0, receipt_1, ..., receipt_k]
```

Each receipt references the previous, forming a tamper-evident chain.

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ Receipt: Immutable step record, hash-chain linked,        │
│          replay-verifiable, canonical encoding             │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification
- [`10_conformance_tests.md`](10_conformance_tests.md) - Test vectors
- [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) - Encoding

---

*Every step is recorded. Every record is verifiable.*
