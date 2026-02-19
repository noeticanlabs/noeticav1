# PhaseLoom Receipt Contract — coh.receipt.pl.v1

**Canon Doc Spine v1.0.0** — Section 12

---

## 1. Schema Overview

### 1.1 Receipt Identifier

`coh.receipt.pl.v1`

### 1.2 Extension

This schema extends the base NK-1 ReceiptCanon schema with PhaseLoom-specific fields.

---

## 2. Required Fields

### 2.1 Schema and Version

| Field | Type | Description |
|-------|------|-------------|
| schema | string | "coh.receipt.pl.v1" |
| version | string | "1.0.0" |

### 2.2 Context IDs

| Field | Type | Description |
|-------|------|-------------|
| coh_object_id | string | Coh object reference |
| ck0_contract_id | string | CK-0 contract reference |
| nk1_policy_id | string | NK-1 policy bundle |
| nk2_scheduler_id | string | NK-2 scheduler |
| params_id | string | Parameter bundle ID |

### 2.3 Clocks

| Field | Type | Description |
|-------|------|-------------|
| clock_timestamp | uint64 | Wall timestamp |
| clock_step | uint64 | Step counter |

### 2.4 Boundary Values

| Field | Type | Description |
|-------|------|-------------|
| state_hash_prev | hash | Previous state hash |
| state_hash_next | hash | Next state hash |
| v_prev | fixed | Violation before |
| v_next | fixed | Violation after |
| C_prev | fixed | Curvature before |
| C_next | fixed | Curvature after |
| T_prev | fixed | Tension before |
| T_next | fixed | Tension after |
| b_prev | fixed | Budget before |
| b_next | fixed | Budget after |
| a_prev | fixed | Authority before |
| a_next | fixed | Authority after |

### 2.5 Derived Deltas

| Field | Type | Description |
|-------|------|-------------|
| delta_T_inc | fixed | Tension increment |
| delta_T_res | fixed | Tension resolution |
| delta_v | fixed | Violation change |
| A | fixed | Amplification |
| D | fixed | Dissipation |

### 2.6 Step Type

| Field | Type | Values |
|-------|------|--------|
| step_type | enum | SOLVE, REPAIR, RESOLVE, AUTH_INJECT |

### 2.7 Authorization

| Field | Type | Description |
|-------|------|-------------|
| multisig | object | Multi-signature (AUTH_INJECT only) |

### 2.8 Compression

| Field | Type | Description |
|-------|------|-------------|
| merkle_root | hash | Merkle root (when compressed) |
| receipt_count | uint | Number of receipts in slab |

---

## 3. Canonical Encoding Rules

### 3.1 Fixed-Point Encoding

All fixed-point values encode as:
```json
{
  "value": "1000000",
  "scale": 6
}
```
Or simplified: "1000000" (implies scale 6)

### 3.2 JSON Serialization

```python
def canon_json(receipt: dict) -> bytes:
    """Serialize receipt to canonical JSON."""
    
    # 1. Sort keys lexicographically
    # 2. No whitespace
    # 3. UTF-8 encoding
    # 4. Numbers as strings (fixed-point)
    
    return json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode('utf-8')
```

### 3.3 Digest Computation

```python
def receipt_digest(receipt: dict) -> str:
    """Compute receipt digest."""
    data = canon_json(receipt)
    return 'h:' + sha3_256(data).hexdigest()
```

---

## 4. Acceptance Conditions

### 4.1 Boundary Matching

- `state_hash_prev` must match previous receipt's `state_hash_next`
- All prev values must match previous state

### 4.2 Recurrence Verification

```python
def verify_curvature(C_prev, C_next, A, D, rho_C):
    """Verify C^+ = rho_C * C + (A - D)"""
    expected = rho_C * C_prev + (A - D)
    return C_next == expected

def verify_tension(T_prev, T_next, delta_T_inc, delta_T_res, rho_T):
    """Verify T^+ = rho_T * T + delta_T_inc - delta_T_res"""
    expected = rho_T * T_prev + delta_T_inc - delta_T_res
    return T_next == expected
```

### 4.3 Budget Charge

```python
def verify_budget_charge(delta_b, A, delta_T_inc, kappa_A, kappa_T):
    """Verify Δb ≥ κ_A * A + κ_T * ΔT_inc"""
    required = kappa_A * A + kappa_T * delta_T_inc
    return delta_b >= required
```

### 4.4 Interlock

```python
def verify_interlock(step_type, A, b, b_min):
    """Verify interlock constraints."""
    if step_type == StepType.SOLVE and A > 0:
        return b > b_min
    return True
```

### 4.5 Authority Injection

```python
def verify_auth_inject(receipt):
    """Verify AUTH_INJECT constraints."""
    if receipt['step_type'] == 'AUTH_INJECT':
        return (
            receipt['delta_b_inj'] > 0 and
            receipt['delta_a_inj'] > 0 and
            receipt['v_prev'] == receipt['v_next'] and
            receipt['multisig'].is_valid()
        )
    return True
```

---

## 5. Full Schema Example

```json
{
  "schema": "coh.receipt.pl.v1",
  "version": "1.0.0",
  "context": {
    "coh_object_id": "coh:abc123",
    "ck0_contract_id": "ck0:def456",
    "nk1_policy_id": "nk1:ghi789",
    "nk2_scheduler_id": "nk2:jkl012",
    "params_id": "params:v1"
  },
  "clocks": {
    "timestamp": 1700000000,
    "step": 42
  },
  "boundary": {
    "state_hash_prev": "h:abc123...",
    "state_hash_next": "h:def456...",
    "v_prev": "1000000",
    "v_next": "800000",
    "C_prev": "0",
    "C_next": "200000",
    "T_prev": "0",
    "T_next": "50000",
    "b_prev": "10000000",
    "b_next": "9500000",
    "a_prev": "0",
    "a_next": "0"
  },
  "derived": {
    "delta_T_inc": "50000",
    "delta_T_res": "0",
    "delta_v": "-200000",
    "A": "0",
    "D": "200000"
  },
  "step_type": "SOLVE",
  "metadata": {
    "receipt_id": "rcpt:xyz789",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

## 6. Receipt Chain

### 6.1 Chain Structure

Receipts form a linked list:
```
receipt[0] -> receipt[1] -> receipt[2] -> ...
```

Each receipt references previous via `state_hash_prev`.

### 6.2 Continuity Verification

```python
def verify_chain(receipts: List[Receipt]) -> bool:
    """Verify receipt chain continuity."""
    for i in range(1, len(receipts)):
        if receipts[i].state_hash_prev != receipts[i-1].state_hash_next:
            return False
    return True
```

---

## 7. Status

- [x] Schema fields defined
- [x] Encoding rules specified
- [x] Acceptance conditions listed
- [ ] Implementation in src/phaseloom/receipt.py

---

*The receipt contract provides cryptographic evidence for all PhaseLoom state transitions, enabling deterministic verification of the extended system dynamics.*
