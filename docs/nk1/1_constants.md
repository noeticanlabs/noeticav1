# NK-1 Locked Constants (v1.0)

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`../ck0/B_reference_constants.md`](../ck0/B_reference_constants.md)

---

## Overview

NK-1 defines its own set of **canon-fixed constants** that must not change without a major version bump. These constants are distinct from (but aligned with) CK-0 constants.

---

## Numeric Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `M_ENTRY_MODE` | `rational_scaled.v1` | Matrix entry representation |
| `M_SYMMETRY_MODE` | `symmetric.v1` | Require M_{ij} = M_{ji} |
| `M_DOMAIN_MODE` | `blocks_only.v1` | Indices are block indices only |
| `DEBT_SCALE` | `6` | Decimal scale for DebtUnit |
| `DEBT_UNIT_TYPE` | `"q:6:<signed_int>"` | Canonical DebtUnit encoding |
| `ROUNDING_RULE` | `half_even.v1` | Banker's rounding |
| `REJECT_ON_NEGATIVE_M` | `true` | Matrix magnitudes must be ≥ 0 |

---

## DebtUnit Definition

DebtUnit is the **only authoritative scalar** in NK-1.

### Representation

Any scalar `x` is represented as:

```
DebtUnit := "q:6:<signed_int>"
```

Where:
- `scale = 6` (fixed decimal places)
- `int_value = round_half_even(x * 10^scale)`

### Construction Rules

1. **Preferred inputs**: Rationals and integers (avoid floats)
2. **If float imported**: Convert via `round_half_even(x * 10^6)`
3. **Canonical encoding**: String format `"q:6:<signed_int>"`

---

## Weight Canonicalization

All weight fractions MUST be reduced before use:

```
w_k = p_k / q_k  →  reduce by gcd(p_k, q_k) = 1
```

### LCM Aggregation

When combining weights, compute Q as:

```
Q = lcm({q_k})  via integer lcm rule
```

Q is used only for deterministic intermediate representation.

---

## Hash Algorithm

| Constant | Value | Description |
|----------|-------|-------------|
| `NK1_HASH_ALGO` | `SHA3_256` | Primary hash algorithm |
| `NK1_HASH_OUTPUT_BITS` | `256` | Output size in bits |
| `NK1_HASH_CHAIN` | `linked` | Hash chain structure |

---

## Version Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `NK1_VERSION_MAJOR` | `1` | Major version |
| `NK1_VERSION_MINOR` | `0` | Minor version |
| `NK1_VERSION_PATCH` | `0` | Patch version |
| `NK1_VERSION_STRING` | `1.0.0` | Full version string |

---

## Action Schema Version

| Constant | Value | Description |
|----------|-------|-------------|
| `NK1_ACTION_SCHEMA_VERSION` | `1` | Current action schema version |
| `NK1_ACTION_ENCODING` | `JSON` | Canonical encoding |
| `NK1_ACTION_FIELD_ORDER` | `lexicographic` | Deterministic field ordering |

---

## Receipt Schema Version

| Constant | Value | Description |
|----------|-------|-------------|
| `NK1_RECEIPT_VERSION` | `1` | Current receipt schema version |
| `NK1_RECEIPT_ENCODING` | `JSON` | Canonical encoding |
| `NK1_RECEIPT_FIELD_ORDER` | `lexicographic` | Deterministic field ordering |

---

## PolicyBundle Registry (§1.8)

The PolicyBundle registry provides chain-wide policy identification and immutability enforcement.

### PolicyBundle Object

| Field | Type | Description |
|-------|------|-------------|
| `policy_bundle_id` | `string` | Unique identifier (UUID v4 format) |
| `policy_digest` | `string` | SHA256 hex of `canon_policy_bytes.v1` |
| `canon_policy_bytes.v1` | `bytes` | Canonical byte representation of policy |

### Construction

```
policy_digest = SHA256(canon_policy_bytes.v1)
```

Where `canon_policy_bytes.v1` is the deterministic, canonical serialization of the policy document.

### Chain-Wide Lock Rule

**v1.0 Lock**: Commit receipts MUST bind `(policy_bundle_id, policy_digest)`.

| Rule | Description |
|------|-------------|
| **Binding** | Every commit receipt must include both `policy_bundle_id` and `policy_digest` |
| **Immutability** | v1.0 forbids transitions that change the `policy_digest` |
| **Rejection** | Any commit with a different digest than the chain's committed digest = REJECT |

#### Transition Rule

```
IF commit_receipt.policy_digest ≠ chain_policy_digest
   THEN REJECT transition
```

This ensures policy drift is impossible across commits - the chain maintains a single canonical policy digest for its entire lifetime.

---

## Change Policy

1. Any change to locked constants requires NK-1 version bump
2. Breaking changes bump MAJOR version
3. Additive changes bump MINOR version
4. Bug fixes bump PATCH version

---

*See also: [`2_debtunit.md`](2_debtunit.md), [`../ck0/B_reference_constants.md`](../ck0/B_reference_constants.md)*
