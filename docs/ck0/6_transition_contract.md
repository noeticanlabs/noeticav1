# CK-0 Transition Contract

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_state_space.md`](1_state_space.md), [`5_curvature_interaction_bounds.md`](5_curvature_interaction_bounds.md)

---

## Overview

The **transition contract** defines how the system state evolves deterministically from step `k` to step `k+1`. This is the core evolution rule of CK-0.

---

## Transition Definition

```
x_{k+1} = T(x_k, u_k)
```

Where:
- `x_k` is the state at step `k`
- `u_k` is the action descriptor at step `k`
- `T` is the deterministic transition function

---

## Requirements

### Purity
- `T` must be **pure** (no hidden state)
- Same `(x_k, u_k)` always produces same `x_{k+1}`

### Deterministic Arithmetic
- All operations must be deterministic
- No floating-point non-determinism
- See [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md)

### Stable Serialization
- State encoding must be canonical
- Hash must match canonical encoding

---

## Action Descriptor

The action `u_k` contains:

| Field | Type | Description |
|-------|------|-------------|
| `action_type` | String | Type of action |
| `parameters` | Map | Action-specific parameters |
| `canonical_encoding` | Bytes | Canonical byte encoding |

### Allowed Actions

CK-0 does not prescribe specific actions. Allowed actions include:

- **Service actions:** Apply budget to reduce debt
- **Query actions:** Read state without modification
- **Patch actions:** Apply modifications to state
- **Governance actions:** Update contract set

---

## Transition Contract Specification

A transition contract must declare:

### T1: Domain
```
domain: X × U → X
```

### T2: Determinism
```
∀x,u: T(x,u) is deterministic
```

### T3: Bounds (optional)
```
||T(x,u) - x|| ≤ Δ_max (for all x,u in domain)
```

### T4: Lipschitz Constant (for NEC)
```
||T(x,u) - T(y,u)|| ≤ L_T·||x - y||
```

---

## Patch Application

Patches are applied as:

```
x_{k+1} = apply_patch(x_k, patch)
```

Where `apply_patch` is part of the transition contract.

### Patch Format

```json
{
  "patch_type": "update_field",
  "field": "budget",
  "value": 100,
  "operation": "set"
}
```

---

## Canonical Transition

### Encoding Order

Fields in `u_k` must be encoded in lexicographic order.

### Hash Computation

```
action_hash = H(canonical_encoding(u_k))
```

---

## Receipt Requirements

Each receipt must include:

| Field | Type | Description |
|-------|------|-------------|
| `state_before` | Hash | `H(x_k)` |
| `state_after` | Hash | `H(x_{k+1})` |
| `action_hash` | Hash | `H(u_k)` |
| `transition_spec_id` | String | Transition contract ID |
| `determinism_check` | Boolean | Whether determinism verified |

---

## Verification

The verifier checks:

1. `state_after == H(T(state_before, action))`
2. Transition is within declared bounds
3. Determinism holds (same input → same output)

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ Transition: x_{k+1} = T(x_k, u_k)                         │
│            pure, deterministic, canonicalizable            │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) - Arithmetic rules
- [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) - Receipts
- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification

---

*Every transition is deterministic and replay-verifiable.*
