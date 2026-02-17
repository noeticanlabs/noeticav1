# CK-0 Allocation Failure Handling

**Version:** 1.0  
**Status:** Canonical  
**Phase:** Phase 0 (Pre-Build Tightening)  
**Related:** [`F_failure_semantics.md`](F_failure_semantics.md), [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md)

---

## Overview

This document defines the deterministic halt behavior when memory allocation fails during canonicalization paths in CK-0. Allocation failure is **not** a best-effort degradation scenario—it is a hard cap violation that terminates execution deterministically.

---

## 1. Allocation Failure is Deterministic Cap Halt

### 1.1 Definition

**Allocation Failure:** Any attempt by `canon_state_bytes()` or related canonicalization functions to allocate memory (heap, stack, or fixed buffers) that fails due to insufficient resources.

### 1.2 Behavioral Contract

| Behavior | Specification |
|----------|---------------|
| **Response** | Deterministic halt immediately upon allocation failure |
| **Recovery** | NONE. No retry, no fallback, no graceful degradation |
| **Classification** | RESOURCE_CAP_MODE violation |
| **Error Code** | `ALLOC_FAILURE` |

### 1.3 Rationale

Canonicalization must produce deterministic, reproducible outputs. If allocation fails during canonicalization:

- The system cannot guarantee a valid canonical form
- Partial state may exist that could cause non-deterministic replay
- Continuing would violate the anti-wedgeability contract

Therefore: **halt is the only correct response**.

---

## 2. Canon State Bytes Allocation

### 2.1 canon_state_bytes() Function

The function `canon_state_bytes(state)` is responsible for producing the canonical byte representation of a CK-0 state. It performs:

1. Rational number reduction
2. Integer encoding (no leading zeros)
3. JSON field ordering (lexicographic)
4. Hash input encoding

### 2.2 Allocation Points

| Operation | Allocation Type | Failure Impact |
|-----------|-----------------|----------------|
| Rational reduction buffer | Heap | HALT |
| Integer to string conversion | Heap | HALT |
| JSON object construction | Heap | HALT |
| Hash input buffer | Fixed/Heap | HALT |

### 2.3 Allocation Size Bounds

Canon state bytes allocation size is **bounded deterministically** by:

```
max_canon_state_bytes ≤ CK0_MAX_STATE_FIELDS × (max_field_name_len + max_field_value_len)
```

Implementations MUST enforce pre-allocation bounds checking before attempting allocation. If bounds are exceeded, allocation failure is triggered before any heap request.

---

## 3. Error Code Specification

### 3.1 ALLOC_FAILURE Code

| Field | Value |
|-------|-------|
| `terminal_error_code` | `"ALLOC_FAILURE"` |
| Classification | `RESOURCE_CAP_MODE` violation |
| Pre-state hash | MUST be captured before allocation attempt |

### 3.2 Return Object Schema

```json
{
  "error_version": 1,
  "terminal_error_code": "ALLOC_FAILURE",
  "violation_type": "RESOURCE_CAP_MODE",
  "op_id": "canon_state_bytes",
  "pre_state_hash": "64hexchars",
  "allocation_context": {
    "function": "canon_state_bytes",
    "requested_bytes": "natural",
    "available_bytes": "natural"
  },
  "timestamp": "ISO8601_utc"
}
```

### 3.3 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `error_version` | Natural | Must be `1` |
| `terminal_error_code` | String | Must be `"ALLOC_FAILURE"` |
| `violation_type` | String | Must be `"RESOURCE_CAP_MODE"` |
| `op_id` | OpID | Operation that attempted allocation |
| `pre_state_hash` | Hash | State hash before allocation attempt |
| `allocation_context` | Object | Details of failed allocation |
| `timestamp` | ISO8601 | UTC timestamp of halt |

---

## 4. Referee-Hostile Specification

### 4.1 Anti-Gaming Properties

This specification is **referee-hostile** because:

1. **No Ambiguity:** Allocation either succeeds or halts—never partial success
2. **No Timing Attacks:** Deterministic halt time (or immediate)
3. **No Recovery Bypass:** No fallback path that could be exploited
4. **Verifiable Pre-state:** The pre_state_hash is captured before allocation, enabling exact replay verification

### 4.2 Verifier Requirements

Verifiers MUST reject any execution where:

- Allocation failure during canonicalization was not treated as deterministic halt
- Error code is not `ALLOC_FAILURE`
- Violation type is not `RESOURCE_CAP_MODE`
- Pre-state hash is missing or invalid
- Any partial canonical output was produced before halt

### 4.3 No Best-Effort Clause

> **FORBIDDEN:** Any implementation that:
> - Continues execution after allocation failure
> - Returns partial/garbage canonical output
> - Attempts retry with smaller allocation
> - Falls back to non-canonical representation

These behaviors constitute protocol violations and MUST be rejected by verifiers.

---

## 5. Resource Cap Mode Classification

### 5.1 Why RESOURCE_CAP_MODE

Allocation failure is classified under `RESOURCE_CAP_MODE` because:

1. Memory allocation limits are a form of resource cap
2. The cap is deterministic (fixed bounds)
3. Exceeding the cap triggers deterministic halt
4. This aligns with existing failure semantics in [`F_failure_semantics.md`](F_failure_semantics.md)

### 5.2 Relationship to RESOURCE_CAP_HALT

| Scenario | Error Code | Distinction |
|----------|------------|-------------|
| Runtime resource exhaustion | `RESOURCE_CAP_HALT` | General cap hit during execution |
| Canon allocation failure | `ALLOC_FAILURE` | Specific to canonicalization path |

Both fall under `RESOURCE_CAP_MODE` violation category.

---

## 6. Implementation Requirements

### 6.1 Pre-allocation Bounds Check

Before any allocation in canonicalization path:

```
if (required_bytes > MAX_ALLOCATION_BOUND) {
    return ALLOC_FAILURE;
}
```

### 6.2 Null Check After Allocation

After successful allocation (if language requires):

```
if (ptr == NULL) {
    return ALLOC_FAILURE;
}
```

### 6.3 Pre-state Hash Capture

The pre_state_hash MUST be captured **before** the allocation attempt:

```
pre_state_hash = compute_state_hash(current_state);
result = canon_state_bytes(current_state);  // May return ALLOC_FAILURE
```

---

## 7. Related Documents

- [`F_failure_semantics.md`](F_failure_semantics.md) - General failure return object semantics
- [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) - Canonicalization rules
- [`B_reference_constants.md`](B_reference_constants.md) - Reference constants

---

*Allocation failure is not a recoverable error. It is a deterministic cap halt that terminates canonicalization definitively.*
