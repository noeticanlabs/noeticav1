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

## Convergence Theorems: Minimal Conditions for Global Asymptotic Coherence

We derive the "smallest honest" conditions under which $D_k \to 0$ (or to a bound) for general nonlinear $S$.

We work with the canonical law:

$D_{k+1} \le D_k - S(D_k,B_k) + E_k$

with:
- $D_k \ge 0$,
- $0 \le S(D,B) \le D$,
- $S$ monotone non-decreasing in $D$ and $B$,
- disturbance policy DP0/DP1/DP2/DP3 (see [`4_budget_debt_law.md`](4_budget_debt_law.md)).

### C.1 Bounded-debt theorem (global; minimal)

**Assume:**
1. $E_k \le \bar{E}$ (DP1/DP2/DP3 implies this via bound).
2. There exists $B_{min} > 0$ and $\alpha \in (0,1)$ such that for all $D \ge 0$:
   $S(D, B) \ge (1-\alpha)D \quad \text{whenever } B \ge B_{min}.$
   Equivalently,
   $D - S(D,B) \le \alpha D \quad (B \ge B_{min}).$

**Then:** whenever $B_k \ge B_{min}$ for all sufficiently large $k$:

$\limsup_{k\to\infty} D_k \le \frac{\bar{E}}{1-\alpha}.$

This is the engine-agnostic stability envelope, and it holds for nonlinear $S$.

### C.2 Asymptotic coherence to zero (DP0, no disturbance)

**Assume DP0:** $E_k \equiv 0$.

Minimal sufficient condition for $D_k \to 0$ is: **uniform fractional service eventually**.

There exists $B_{min} > 0$ and $\eta \in (0,1)$ such that for all $D > 0$:

$S(D,B) \ge \eta D \quad \text{whenever } B \ge B_{min}.$

If $B_k \ge B_{min}$ for all sufficiently large $k$, then:

$D_{k+1} \le (1-\eta)D_k \quad\Rightarrow\quad D_k \to 0 \text{ exponentially.}$

This is the clean "global asymptotic coherence" condition.

### C.3 Asymptotic coherence with vanishing disturbance

If $E_k \to 0$ (or $\sum_k E_k < \infty$), and the same fractional service condition holds eventually, then:

$D_k \to 0.$

A standard sufficient condition:
- DP2 with event schedule that eventually stops disturbances,
- or DP3 where modeled error decays under refinement.

### C.4 "Integral" condition (weaker, more general)

If you can't guarantee uniform fractional service, you can still get convergence if service is **persistently positive** away from zero.

**Assume DP0 and:**

For every $\varepsilon > 0$, there exists $s_\varepsilon > 0$ such that:

$S(D,B_{min}) \ge s_\varepsilon \quad \forall D \ge \varepsilon.$

Then debt cannot stall above $\varepsilon$. It must eventually enter $[0, \varepsilon]$. Since $\varepsilon$ is arbitrary:

$D_k \to 0.$

This is a minimal "no-flat-plateaus" condition on $S$.

### C.5 Necessary condition (what must be true)

If DP0 and $D_k \to 0$ for all initial debts, then it is necessary that:

$S(D,B_{min}) > 0 \quad \forall D>0$

for some persistent budget level $B_{min}$ that occurs infinitely often.

If $S(D,B)=0$ on any interval $D \in (\varepsilon, M)$ for the budgets you actually use, the system can get stuck there forever. No theorem can save you.

### C.6 What CK-0 should record for these theorems to apply

To make these convergence claims auditable, CK-0 receipts/policy headers must pin:
- whether DP0/DP1/DP2/DP3 is active,
- bounds $\bar{E}$ (or event bounds),
- a service envelope certificate, e.g.:
  - $\alpha$ and $B_{min}$ such that $D-S(D,B) \le \alpha D$ for $B \ge B_{min}$,
  - or a declared $S(D,B_{min}) \ge s_\varepsilon$ schedule (less common).

This is how "math claims" become "verifier-checkable claims."

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
