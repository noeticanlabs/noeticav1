# CK-0 Failure Semantics

**Version:** 1.0  
**Status:** Canonical  
**Phase:** Phase 0 (Pre-Build Tightening)

---

## Overview

This document defines the exact failure return object semantics for CK-0 runtime halt conditions. All failure scenarios must adhere precisely to these semantics. Deviation constitutes a protocol violation and will be rejected by verifiers.

---

## Failure Scenarios

### 1. Resource Cap Halt

**Trigger:** Execution reaches a resource cap that cannot be satisfied.

**Return Object:**

| Field | Type | Description |
|-------|------|-------------|
| `terminal_error_code` | String | `"RESOURCE_CAP_HALT"` |
| `op_id` | OpID | Identifier of the operation that caused the halt |
| `pre_state_hash` | Hash | State hash before the failing operation attempted execution |

**Conditions:**
- Resource cap includes: memory allocation, computation budget, fuel limits
- The pre_state_hash MUST reflect the state at the moment the cap was hit
- No partial state mutations are committed

---

### 2. Singleton Failure Halt

**Trigger:** A singleton operation (exactly-one-required) fails to execute.

**Return Object:**

| Field | Type | Description |
|-------|------|-------------|
| `terminal_error_code` | String | `"SINGLETON_FAILURE"` |
| `op_id` | OpID | Identifier of the singleton operation that failed |
| `pre_state_hash` | Hash | State hash before the failing singleton was attempted |

**Conditions:**
- Singleton operations are those marked with cardinality "exactly one"
- Failure includes: unsatisfied preconditions, missing dependencies, type errors
- The pre_state_hash MUST reflect the state when the singleton was evaluated

---

### 3. Policy Veto

**Trigger:** A policy check explicitly rejects the operation.

**Return Object:**

| Field | Type | Description |
|-------|------|-------------|
| `terminal_error_code` | String | `"POLICY_VETO"` |
| `op_id` | OpID | Identifier of the vetoed operation |
| `pre_state_hash` | Hash | State hash before the policy-vetoed operation |

**Conditions:**
- Policy includes: security policies, capability policies, governance rules
- The policy_id SHOULD be derivable from the op_id
- The pre_state_hash MUST reflect the state before the vetoed operation

---

## Error Object Schema

All failure return objects MUST conform to this schema:

```json
{
  "error_version": 1,
  "terminal_error_code": "RESOURCE_CAP_HALT | SINGLETON_FAILURE | POLICY_VETO",
  "op_id": "op_id_string",
  "pre_state_hash": "64hexchars",
  "timestamp": "ISO8601_utc",
  "error_context": {}
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `error_version` | Natural | Must be `1` for this specification |
| `terminal_error_code` | String | One of the three codes defined above |
| `op_id` | OpID | The operation that caused the halt |
| `pre_state_hash` | Hash | State hash before the failing operation (64 hex chars, lowercase) |
| `timestamp` | ISO8601 | UTC timestamp of halt (for logging only, not for verification) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `error_context` | Map | Additional diagnostic information (MUST be empty for verifier acceptance) |

---

## Non-Mutability Contract

### Error is NOT Ledger-Mutating

When a failure occurs:

1. The pre_state_hash is captured BEFORE any mutation attempt
2. The state remains unchanged - no fields are modified
3. No contracts are activated or deactivated
4. No debt/budget/disturbance values are altered

```
┌─────────────────────────────────────────────────────────────┐
│  FAILURE PATH (NO STATE CHANGE)                             │
│                                                             │
│  state_k → [validate] → [execute] → FAILURE                │
│                ↓                                            │
│           state_k (UNCHANGED)                              │
│                                                             │
│  Return: {terminal_error_code, op_id, state_k_hash}        │
└─────────────────────────────────────────────────────────────┘
```

### Error is NOT Receipted

**Critical Rule:** No receipt is emitted for failed operations.

- The Ω-ledger does NOT contain an entry for the failed operation
- The step_index does NOT increment
- The receipt_chain_hash does NOT advance

This is intentional. A receipt represents a successful state transition. Failure is not a transition.

---

## Parent Commit Receipt Integration

### Error Hash Inclusion

The error object hash MUST be included in the **parent commit receipt** for traceability:

**Parent Receipt Schema Extension:**

```json
{
  "receipt_version": 1,
  "receipt_id": "uuid-v4",
  "step_index": 42,
  
  "state_before": "abc123...",
  "state_after": "def456...",
  
  "child_error_hash": "error_object_hash_or_null",
  "child_error_code": "RESOURCE_CAP_HALT | SINGLETON_FAILURE | POLICY_VETO | null",
  
  /* ... other receipt fields ... */
}
```

### Fields Added

| Field | Type | Description |
|-------|------|-------------|
| `child_error_hash` | Hash or null | Hash of the error object, null if no child error |
| `child_error_code` | String or null | Terminal error code if child error exists, null otherwise |

### Traceability Chain

```
receipt_k → receipt_{k+1}
              ↓
         child_error (not a receipt)
              ↓
         child_error_hash in receipt_{k+1}
```

The error object itself is not a receipt. It is a separate artifact whose hash is recorded in the next successful receipt.

---

## Verifier Rejection Criteria

A verifier MUST reject if:

1. **Mutated State:** The pre_state_hash does not match the actual prior state
2. **Missing Error Hash:** A failure occurred but child_error_hash is null
3. **Invalid Error Code:** terminal_error_code is not one of the three defined codes
4. **Receipt Exists:** A receipt was emitted for a failed operation (violates non-receipting rule)
5. **Hash Mismatch:** The error object hash does not match the recorded child_error_hash

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│  Failure: Terminal error code + op_id + pre_state_hash,    │
│           NOT ledger-mutating, NOT receipted, error hash   │
│           recorded in parent commit receipt                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) - Receipt schema and Ω-ledger
- [`2_invariants.md`](2_invariants.md) - Hard invariants and failure categories
- [`E_capability_ban.md`](E_capability_ban.md) - Capability restrictions
- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification logic

---

*Failure is not a transition. The ledger records only success.*
