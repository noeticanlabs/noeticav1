# CK-0 Reference Constants

**Version:** 1.0  
**Status:** Canonical  
**Applies To:** All CK-0 implementations

---

## Overview

This document defines the canonical constants for CK-0. Any implementation that changes a constant **must** bump the CK-0 version.

---

## Numeric Arithmetic

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_INT_BASE` | 10 | Base for integer representation |
| `CK0_RATIO_REDUCTION` | `lowest_terms` | Rationals must be reduced |
| `CK0_BIGINT_LIMB_BITS` | 64 | Bits per limb for big integers |

---

## Rounding Mode

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_ROUNDING_MODE` | `half_even` | Banker's rounding (default) |
| `CK0_ROUNDING_PRECISION` | `unbounded` | No precision limit by default |

---

## Debt and Budget Scaling

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_DEBT_UNIT_SCALE` | 1 | Debt stored in base units (no scaling) |
| `CK0_DEBT_UNIT_TYPE` | `integer` | Integer-only debt |
| `CK0_BUDGET_UNIT_SCALE` | 1 | Budget in base units |
| `CK0_MAX_DEBT` | `unbounded` | No hard cap (controlled by invariant) |
| `CK0_MIN_BUDGET` | 0 | Minimum allowed budget |

---

## Hash Algorithm

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_HASH_ALGO` | `SHA3_256` | Primary hash algorithm |
| `CK0_HASH_OUTPUT_BITS` | 256 | Output size in bits |
| `CK0_RECEIPT_HASH_CHAIN` | `linked` | Hash chain structure |

---

## Violation Functional

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_V_POLICY_DEFAULT` | `CK0.v1` | Default squared norm policy |
| `CK0_V_NORM_DEFAULT` | `l2` | Default ℓ₂ norm |
| `CK0_V_WEIGHT_DOMAIN` | `nonnegative_real` | Allowed weight values |
| `CK0_V_SIGMA_DOMAIN` | `positive_real` | Normalizer must be positive |

---

## Servicing Map

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_SVC_DEFAULT` | `CK0.svc.lin` | Default linear capped servicing |
| `CK0_SVC_EFFICIENCY_DEFAULT` | 1.0 | Default μ = 1.0 (full service) |
| `CK0_SVC_EFFICIENCY_MIN` | 0.0 | Minimum efficiency |
| `CK0_SVC_EFFICIENCY_MAX` | 1.0 | Maximum efficiency |

---

## Receipt Schema

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_RECEIPT_VERSION` | 1 | Current receipt schema version |
| `CK0_RECEIPT_ENCODING` | `JSON` | Canonical encoding |
| `CK0_RECEIPT_FIELD_ORDER` | `lexicographic` | Deterministic field ordering |
| `CK0_RECEIPT_HASH_INCLUDES` | `[prev_hash, state_before, state_after, action, budget, debt_before, debt_after]` | Fields in hash |

---

## Invariant Categories

| Category Code | Description |
|---------------|-------------|
| `INV_TERMINAL` | Failure is terminal (abort) |
| `INV_REPAIRABLE` | Failure triggers repair mode |
| `INV_WARNING` | Warning only (non-terminal) |

---

## Versioning

| Constant | Value | Description |
|----------|-------|-------------|
| `CK0_VERSION_MAJOR` | 1 | Major version |
| `CK0_VERSION_MINOR` | 0 | Minor version |
| `CK0_VERSION_PATCH` | 0 | Patch version |
| `CK0_VERSION_STRING` | `1.0.0` | Full version string |

---

## Change Policy

1. Any change to constants requires CK-0 version bump
2. Breaking changes bump MAJOR version
3. Additive changes bump MINOR version
4. Bug fixes bump PATCH version

---

*See also: [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md)*
