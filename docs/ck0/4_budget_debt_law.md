# CK-0 Budget/Debt Law

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`3_violation_functional.md`](3_violation_functional.md)

---

## Overview

The **Law of Coherence** defines how debt evolves through service and disturbance. This is the core dynamical law that makes CK-0 enforceable.

---

## Definitions

### Debt
```
D_k := V(x_k)
```
The debt at step `k` is the violation functional value.

### Budget
```
B_k ≥ 0
```
The declared service capacity for step `k`.

### Disturbance
```
E_k ≥ 0
```
The declared disturbance bound for step `k`.

---

## Servicing Map

Define a **servicing map** `S(D, B)` that models how budget reduces debt:

```
Φ(D, B) := D - S(D, B)
```

### CK-0 Constraints on S

| Constraint | Expression | Description |
|------------|------------|-------------|
| No free service | `S(D, 0) = 0` | Zero budget means zero service |
| Non-negativity | `0 ≤ S(D, B) ≤ D` | Cannot service below zero |
| Monotonicity | `S` monotone non-decreasing in `D` and `B` | More debt/budget = more service |

---

## Service Law Admissibility Conditions (A1-A6)

A service law `Φ : ℝ_{≥0} × ℝ_{≥0} → ℝ_{≥0}` is **admissible** iff it satisfies the following conditions:

| ID | Condition | Expression | Description |
|----|-----------|------------|-------------|
| **A1** | Determinism | Computable under canonical arithmetic | Replay-identical results |
| **A2** | Monotonicity | `Φ` monotone non-decreasing in `D`, non-increasing in `B` | Budget reduces debt |
| **A3** | Zero-debt consistency | `Φ(0, B) = 0` | No debt means no service needed |
| **A4** | Zero-budget identity | `Φ(D, 0) = D` | No budget means no debt change |
| **A5** | Lipschitz control | `|Φ(D₁,B) - Φ(D₂,B)| ≤ L|D₁-D₂|` | Bounded sensitivity to debt |
| **A6** | Continuity | Continuous or piecewise continuous | No sudden jumps |

### Derivation from S to Φ

The service law is defined via the servicing map `S`:

```
Φ(D, B) := D - S(D, B)
```

The constraints on `S` imply the admissibility conditions on `Φ`:

| From S constraint | Derives to Φ condition |
|-------------------|------------------------|
| `S(D, 0) = 0` | `Φ(D, 0) = D` (A4) |
| `0 ≤ S(D, B) ≤ D` | `0 ≤ Φ(D, B) ≤ D` |
| Monotone in D, B | A2 (monotonicity) |

### Policy IDs

| Policy | ID | Description |
|--------|-----|-------------|
| Service policy | `CK0.service.v1` | Default CK-0 service policy |
| Instance (linear) | `linear_capped.mu:<value>` | Linear capped servicing |

---

## Canonical CK-0 Law

```
┌─────────────────────────────────────────────────────────────┐
│  D_{k+1} ≤ D_k - S(D_k, B_k) + E_k                        │
│                                                             │
│  with E_k ≥ 0 declared and bounded                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Identity

With the constraint `S(D, 0) = 0`:
```
Φ(D, 0) = D - S(D, 0) = D
```

**This is the disturbance-separated form.** All "stuff that happens to you" lives in `E_k`, not secretly inside `Φ`.

---

## Why Disturbance Separation?

| Property | Benefit |
|----------|---------|
| Audit clarity | "Decrease comes only from service; increase comes only from declared disturbance" |
| No double-counting | `Φ` is purely service; `E_k` is purely disturbance |
| Replay stability | Easy to verify inequality in fixed-point arithmetic |
| General | Allows linear, saturating, trust-region, and nonlinear `S` |

---

## Default Servicing Function

### Linear Capped Servicing (CK-0.v1.default)

```
S_lin(D, B) := min(D, μ · B)
```

Where `μ ∈ [0, 1]` is the service efficiency.

### Resulting Law

```
D_{k+1} ≤ D_k - min(D_k, μ · B_k) + E_k
```

**Properties:**
- Never services below zero
- Respects `S(D, 0) = 0`
- Bounded service rate

---

## Abort Rules

The system MUST abort if:

| Condition | Action |
|-----------|--------|
| `D_k > D_max` (if defined) | Terminal invariant failure |
| Invariant `I(x_k) = false` | Abort (per invariant policy) |
| `B_k < 0` | Invalid (invariant failure) |
| `E_k < 0` | Invalid (invariant failure) |

---

## Disturbance Accounting Rule

> **Critical:** Either `E_k` is logged explicitly (even if 0), or the verifier assumes `E_k = 0` by policy. No silent disturbances.

This rule prevents the classic loophole where `E_k` becomes an unbounded "excuse field" for uncooperative behavior.

| Policy | Behavior | Risk |
|--------|----------|------|
| **Explicit logging** | `E_k` always recorded in receipt | Low (full audit trail) |
| **Zero assumption** | Verifier assumes `E_k = 0` | Medium (no disturbance allowed) |

### Implementation Requirements

1. **Explicit logging mode:**
   - `E_k` MUST be present in every receipt
   - If no disturbance occurs, log `E_k = 0`
   - Verifier checks `E_k ≥ 0`

2. **Zero-assumption mode:**
   - Disturbance field may be omitted from receipt
   - Verifier treats missing field as `E_k = 0`
   - Policy must be declared in contract metadata

### Why This Matters

Without this rule, a malicious actor could:
1. Claim arbitrary positive `E_k` to justify debt increases
2. Never actually log disturbance values
3. Use `E_k` as an unbounded excuse field

The disturbance accounting rule closes this loophole by requiring either explicit logging or zero assumption.

---

## Boundedness Lemma

**Lemma:** Under bounded disturbance `E_k ≤ Ē` and non-negative budgets, the debt is bounded.

**Proof sketch:**
```
D_{k+1} ≤ D_k - S(D_k, B_k) + E_k
        ≤ D_k + Ē
```

By induction:
```
D_k ≤ D_0 + k · Ē
```

If budgets are also bounded and service is effective (`S ≥ c · B` for some `c > 0`), debt remains bounded even with continuous disturbance.

---

## Exact Rounding and Units

All comparisons in the law use:

- **Integer arithmetic** (DebtUnit = integer)
- **Canonical rounding** (see [`7_rounding_canonicalization.md`](7_rounding_canonicalization.md))
- **No floating-point** in inequality verification

---

## Receipt Requirements

Each receipt must include:

| Field | Type | Description |
|-------|------|-------------|
| `debt_before` | DebtUnit | `D_k` |
| `debt_after` | DebtUnit | `D_{k+1}` |
| `budget` | BudgetUnit | `B_k` |
| `disturbance` | DisturbanceUnit | `E_k` |
| `service_applied` | DebtUnit | `S(D_k, B_k)` |
| `law_satisfied` | Boolean | `D_{k+1} ≤ D_k - S(D_k, B_k) + E_k` |

---

## Policy IDs

| Policy | ID | Description |
|--------|-----|-------------|
| Servicing (linear) | `CK0.svc.lin` | Linear capped servicing |
| Servicing (custom) | `CK0.svc.<id>` | Custom servicing map |

---

## No Hidden Slack

Implementations MUST:
- Log `E_k` explicitly (even if zero)
- Optionally enforce `E_k ≤ Ē` by verifier policy

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ CK-0 Law: D_{k+1} ≤ D_k - S(D_k, B_k) + E_k               │
│           with S(D,0)=0, S(D,B)∈[0,D], monotone           │
│           (debt ↓ by service; debt ↑ by declared disturbance)│
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`5_curvature_interaction_bounds.md`](5_curvature_interaction_bounds.md) - NEC theorems
- [`6_transition_contract.md`](6_transition_contract.md) - State evolution
- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification

---

*The physics of CK-0: debt goes down only by service; debt goes up only by declared disturbance.*
