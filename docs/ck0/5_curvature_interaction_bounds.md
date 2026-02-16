# CK-0 Curvature Interaction Bounds

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`4_budget_debt_law.md`](4_budget_debt_law.md)

---

## Overview

This document defines the NEC (No-Extraneous-Curvature) closure theorems - the mathematical backbone that prevents "implementation cheating." These bounds provide certificate-side replayable guarantees about curvature interactions.

---

## Purpose

The curvature interaction bounds provide:

1. **Certificate-side replayable bounds** for the verifier
2. **Hessian/curvature interaction bounds** (Lemma 1-style rectangle identity)
3. **Conditions** for regularity, bounded mixed derivatives, locality
4. **Deterministic computation** requirements

---

## Rectangle Identity Bound

### Lemma: Curvature Interaction Bound

For twice-differentiable violation functional `V` and transition `T`:

```
| V(T(x, u)) - V(x) - ∇V(x)·(T(x,u) - x) - ½·(T(x,u) - x)ᵀ·H_V(x)·(T(x,u) - x) | 
≤ C · ||T(x,u) - x||³
```

Where:
- `H_V(x)` is the Hessian of `V` at `x`
- `C` is a bounded curvature constant
- The bound is **deterministically computable** from contract specifications

---

## Assumptions

### A1: Regularity
```
||∂³V/∂x³|| ≤ M_3  (bounded third derivative)
```

### A2: Bounded Mixed Derivatives
```
||∂²T_i/∂x_j∂x_k|| ≤ M_T  (bounded transition second derivatives)
```

### A3: Locality
The transition `T` is locally Lipschitz:
```
||T(x,u) - T(y,u)|| ≤ L_T·||x - y||  for all x,y in domain
```

### A4: Contract Smoothness
Each contract residual `r_k` is twice differentiable with bounded second derivatives.

---

## Certificate-Side Requirements

### What the Verifier Needs

| Input | Source |
|-------|--------|
| `C` (curvature constant) | Computed from contract set |
| `M_3` (third derivative bound) | Declared by contract |
| `M_T` (transition bound) | From transition contract |
| `L_T` (Lipschitz constant) | From transition contract |

### What the Prover Assumes

- Bounds hold over the execution region
- No hidden curvature contributions
- Deterministic bound computation

---

## Deterministic Bound Computation

The bound inputs MUST be computed deterministically:

```
bound = f(contract_set_id, transition_spec_id, domain_bounds)
```

Where `f` is a CK-0 canonical function.

---

## NEC Theorem Statement

**Theorem (NEC Closure):** Under assumptions A1-A4, the curvature interaction bound is **certificate-computable** and **replayable** without trusting the prover.

**Proof sketch:**
1. Contract set defines `V` with declared derivative bounds
2. Transition contract defines `T` with declared Lipschitz bounds
3. Combined bounds yield deterministic `C`
4. Verifier recomputes from receipts + spec

---

## Cross-Domain Applicability

This framework applies to:

- PDE residuals and constraints
- Typed constraints and rail residuals
- Governance and policy compliance
- **Any domain** with declared derivative bounds

---

## Relation to Budget Law

The curvature bounds provide the **theoretical foundation** for the servicing map `S(D, B)`:

```
S(D, B) ≥ c·B  (for some c > 0 under bounded curvature)
```

This ensures the budget law is not just a formal inequality but has **physical meaning**.

---

## Receipt Obligations

| Field | Type | Description |
|-------|------|-------------|
| `curvature_bound_C` | Real | Computed curvature constant |
| `bound_computation_spec` | String | Spec ID used |
| `assumptions_declared` | Array | Assumptions that hold |

---

## Canon One-Line

```
┌─────────────────────────────────────────────────────────────┐
│ NEC: Curvature interaction bound is deterministically     │
│      certificate-computable and replayable               │
│      |ΔV - linear - quadratic| ≤ C·||Δx||³               │
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documents

- [`6_transition_contract.md`](6_transition_contract.md) - Transition definition
- [`9_replay_verifier.md`](9_replay_verifier.md) - Verification
- [`10_conformance_tests.md`](10_conformance_tests.md) - Test vectors

---

*This is the math backbone that prevents implementation cheating.*
