# CK-0 Violation Functional

**Version:** 1.0  
**Status:** Canonical  
**Policy ID:** `CK0.v1`  
**Related:** [`0_overview.md`](0_overview.md), [`2_invariants.md`](2_invariants.md)

---

## Overview

The **violation functional** `V(x)` measures the "soft" coherence of a system state. Together with hard invariants, `V(x)` defines whether a system is coherent.

**Coherence = Invariants satisfied + Violation measured**

---

## Scope and Separation of Concerns

CK-0 partitions constraints into:

### Hard Invariants
- Defined by `I: X → {true, false}`
- If `I(x) = false`, the step is **not coherent**
- Must follow implementation's declared rail policy (REJECT or REPAIR)
- **Not** represented by "infinite debt" inside `V`

### Soft/Graded Contracts
- Measured via residuals and aggregated into `V(x)`
- Zero means "all active contracts satisfied"

---

## Contract Set Definition

CK-0 defines a **finite ordered contract set**:

```
𝒦 = (1, ..., K)
```

Each contract `k ∈ 𝒦` declares:

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique contract identifier |
| `r_k` | `X → ℝ^{m_k}` | Residual map |
| `σ_k` | `X → ℝ_{>0}` or constant | Normalizer (scale) |
| `w_k` | `ℝ_{≥0}` | Weight |
| `A_k` | `X → {true, false}` | Applicability predicate |

**Norm:** Default is ℓ₂, with fixed coordinate chart and ordering.

---

## Canonical Normalization

Define **normalized residual**:

```
r̃_k(x) := r_k(x) / σ_k(x)
```

**Constraint:** If `A_k(x) = true`, then `σ_k(x) > 0`. Violation is a hard invariant failure.

**Division:** Must use canonical arithmetic (see [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md)).

---

## CK-0 Canonical Violation Functional

For any `x ∈ X` such that `I(x) = true`:

```
┌─────────────────────────────────────────────────────┐
│  V(x) := Σ_{k=1}^{K} w_k · ||r̃_k(x)||₂²          │
│                                                     │
│  where r̃_k(x) = r_k(x) / σ_k(x)                   │
│        if A_k(x) = false, then r̃_k(x) ≡ 0       │
└─────────────────────────────────────────────────────┘
```

### Properties

| Property | Value |
|----------|-------|
| Non-negativity | `V(x) ≥ 0` |
| Zero condition | `V(x) = 0` iff every active residual is zero |
| Additivity | Additive across contract sets |
| Smoothness | Smooth when `r_k, σ_k` are smooth |

---

## Determinism Requirements

CK-0 requires that `V(x)` be:

- **Measurable:** Computable from declared contracts and state
- **Replay-stable:** Identical under replay across implementations
- **Canonicalizable:** No wedgeable intermediate representations

### Implementation Rules

1. **No floating-point non-determinism** for authoritative `V` used in gating/receipts
2. **Rational reduction** to lowest terms before aggregation
3. **Rounding mode** must be CK-0-canonical (recorded by policy ID)

---

## Robust Variant (Extension)

CK-0 defines the squared form as canonical. A robust extension `CK0R` MAY be declared:

```
V_R(x) := Σ w_k Σ ρ(r̃_{k,j}(x))
```

Where `ρ` is from an allowlist with declared Lipschitz bounds.

**Policy IDs:**
- `CK0.v1` - Squared default
- `CK0R.v1:<ρ_id>` - Robust variant

---

## Receipt Obligations

Every step that evaluates `V` MUST emit receipt fields:

### Global Fields
| Field | Type | Description |
|-------|------|-------------|
| `state_hash` | Hash | Canonical state hash |
| `contract_set_id` | Hash | Hash of ordered contract list + versions |
| `V_policy_id` | String | Policy used (e.g., "CK0.v1") |
| `V_total` | DebtUnit | Total violation |
| `active_contract_bitmap` | Bitfield | Active contract indicators |

### Per-Contract Fields
| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | String | Contract identifier |
| `m_k` | Natural | Residual dimension |
| `sigma_spec_id` | String | Normalizer spec ID |
| `weight_spec_id` | String | Weight spec ID |
| `r2` | DebtUnit | `||r̃_k||₂²` (required) |
| `r_inf` | DebtUnit | `||r̃_k||_∞` (optional) |
| `r_hash` | Hash | Commitment to full vector (optional) |

---

## Canon One-Line Definition

```
┌─────────────────────────────────────────────────────────────┐
│ CK-0: V(x) = Σ w_k |r_k(x)/σ_k(x)|₂²                       │
│         (hard invariant failures handled by reject/repair,  │
│          not by V)                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`4_budget_debt_law.md`](4_budget_debt_law.md) - Budget/debt update using V
- [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md) - Arithmetic rules
- [`8_receipts_omega_ledger.md`](8_receipts_omega_ledger.md) - Receipt schema

---

*Coherence is measured by V plus invariants.*
