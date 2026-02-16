# CK-0 State Space

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`B_reference_constants.md`](B_reference_constants.md)

---

## Overview

This document defines the state space `X` as a typed product space, including field partitions, serialization contracts, and canonical encoding.

---

## State Space Definition

The CK-0 state space `X` is defined as:

```
X := X_1 × X_2 × ... × X_n
```

Where each `X_i` is a **field block** with its own type.

---

## Field Blocks

### Required Blocks

| Block | Type | Description |
|-------|------|-------------|
| `debt` | `ℤ_{\ge 0}` | Current debt `D_k` |
| `budget` | `ℤ_{\ge 0}` | Declared budget `B_k` |
| `disturbance` | `ℤ_{\ge 0}` | Disturbance bound `E_k` |
| `step_index` | `ℕ` | Current step number |
| `receipt_chain_hash` | `H` | Hash of previous receipt |

### Optional Blocks

| Block | Type | Description |
|-------|------|-------------|
| `solver_state` | `Abstract` | Solver-specific state |
| `contract_set` | `ContractSet` | Active contract definitions |
| `metadata` | `Map(String, Value)` | Arbitrary metadata |

---

## Type Signatures

```
State := {
  debt: Integer,
  budget: Integer, 
  disturbance: Integer,
  step_index: Natural,
  receipt_chain_hash: Hash,
  ...optional_fields
}
```

---

## Domain Bounds

| Field | Lower Bound | Upper Bound | Notes |
|-------|-------------|-------------|-------|
| `debt` | 0 | ∞ (controlled by invariant) | Must satisfy D ≤ D_max if invariant defined |
| `budget` | 0 | ∞ | No upper bound by default |
| `disturbance` | 0 | ∞ | Non-negative |
| `step_index` | 0 | ∞ | Starts at 0 |

---

## Serialization Contract

### Canonical Ordering

Fields **must** be serialized in lexicographic order:

1. `budget`
2. `debt`
3. `disturbance`
4. `receipt_chain_hash`
5. `step_index`
6. ... (any additional fields in sorted order)

### Canonical JSON Encoding

```json
{
  "budget": 100,
  "debt": 5,
  "disturbance": 0,
  "receipt_chain_hash": "abc123...",
  "step_index": 42
}
```

### Byte Order

For binary serialization:
- Little-endian encoding for integers
- Network byte order for hashes

---

## State Snapshot

A **state snapshot** is a canonical encoding of a state that can be hashed. The snapshot includes:

1. All field values in canonical order
2. Field names (for extensibility)
3. No whitespace variations

### Snapshot Hash

```
state_hash := H(canonical_encoding(state))
```

Where `H` is the CK-0 hash algorithm (SHA3_256 by default).

---

## State Validation

A state is **valid** if:

1. All required fields are present
2. All fields satisfy their domain bounds
3. The canonical encoding is deterministic

---

## Extensibility

Additional fields may be added to the state space:

1. Field name must be a valid identifier
2. Field type must be serializable
3. New fields must be optional (backward compatibility)

---

## Related Documents

- [`2_invariants.md`](2_invariants.md) - Hard constraints on state
- [`6_transition_contract.md`](6_transition_contract.md) - State evolution
- [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) - Receipt chaining

---

*CK-0 requires deterministic, replayable state encoding.*
