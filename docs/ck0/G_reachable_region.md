# CK-0 Reachable Region ℛ Definition

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`1_state_space.md`](1_state_space.md), [`2_invariants.md`](2_invariants.md), [`5_curvature_interaction_bounds.md`](5_curvature_interaction_bounds.md), [`6_transition_contract.md`](6_transition_contract.md)

---

## Overview

This document defines the **reachable region** ℛ — the set of states and residual structures that the CK-0 system can legitimately occupy during execution. The reachable region is critical for:

1. **Contract enforceability**: Bounds must be enforceable within ℛ to make contracts mathematically legitimate
2. **Verifier replay**: The region defines what the verifier accepts as valid trajectories
3. **NEC bounds**: Curvature interaction bounds require known geometry limits

In CK-0, the geometry of enforceability lives in the behavior of residuals c_k(x), gradient ∇V(x), and Hessian H_V(x).

---

## What ℛ Is in CK-0

Let ℛ be the **residual contract structure**:

```
ℛ(x) = (c₁(x), c₂(x), ..., c_m(x))
```

Where each c_k(x) is a residual from contract k, and:

```
V(x) = Σ_k w_k · c_k(x)²
```

ℛ must support enough structure to make:
- δ-bounds meaningful
- Batch curvature bounds computable
- Measured gate sound

---

## Option A: Implicit Definition

### Definition

A state `x` and its residual structure `ℛ(x)` are in ℛ if and only if:

1. It is encountered during execution from an initial valid state
2. It passes all active invariants: `I(x) = true` for all `I ∈ Invariants`
3. It was produced by a valid transition: `x = T(x_prev, u)`

### Formal Specification

```
ℛ_A := { (x, ℛ(x)) | ∃ x_0, u_0,...,u_{k-1} such that:
  - x_0 satisfies all invariants
  - ∀ i < k: x_{i+1} = T(x_i, u_i)
  - ∀ i ≤ k: I(x_i) = true for all invariants I }
```

### Required Bounds for Enforceability

Even implicitly, ℛ must support:

| Bound | Symbol | Description |
|-------|--------|-------------|
| **A_max** | Per-operation delta | `|δ_o(x)|_X ≤ A_max(o)` |
| **L_max** | Gradient bound | `|∇V(x)| ≤ L_max` |
| **H_max** | Hessian bound | `|H_V(z)| ≤ H_max` for all z in neighborhood |

### Trade-offs

| Pros | Cons |
|------|------|
| ✓ Flexible; adapts to actual execution | ✗ No pre-execution verification possible |
| ✓ Captures all valid execution paths | ✗ Requires full replay for verification |
| ✓ Simpler initial specification | ✗ Bounds emerge, not declared upfront |

---

## Option B: Explicit Definition

### Definition

A state `x` with residual structure `ℛ(x)` is in ℛ if and only if:

1. **Residual structure**: Each residual c_k(x) is well-defined (C² differentiable)
2. **Gradient bounded**: `|∇V(x)| ≤ L_max`
3. **Curvature bounded**: `|H_V(z)| ≤ H_max` for all z in the convex hull used by scheduling
4. **Step bounded**: Each operation delta satisfies `|δ_o(x)| ≤ A_max`

### Formal Specification

```
ℛ_B := { (x, ℛ(x)) | 
  - ∀ residual c_k: C² differentiable
  - ∃ L_max: |∇V(x)| ≤ L_max
  - ∃ H_max: |H_V(z)| ≤ H_max ∀ z ∈ ℂ(x, B)
  - ∀ op o: |δ_o(x)| ≤ A_max(o)
  - ∀ invariant I: I(x) = true }
```

Where ℂ(x, B) is the convex hull of the scheduling region.

### Required Contract Declarations

| Bound | Symbol | CK-0 Meaning |
|-------|--------|---------------|
| **A_max** | Per-operation delta | Maximum δ an operation may produce |
| **L_max** | Lipschitz constant | `|∇V(x) - ∇V(y)| ≤ L_max·|x-y|` |
| **H_max** | Hessian bound | `sup |H_V(z)| ≤ H_max` in neighborhood |

### Trade-offs

| Pros | Cons |
|------|------|
| ✓ Pre-execution verification possible | ✗ Requires exhaustive bound specification |
| ✓ Enables formal safety proofs | ✗ May be over-restrictive |
| ✓ Supports efficient verifier checks | ✗ Bounds must be proven achievable |
| ✓ Clear rejection criteria | ✗ Version updates may require bound changes |

---

## The Enforceability Triangle

To make CK-0 contracts **enforceable** (not rhetorical), ℛ must satisfy:

| Constant | Controls | Why Needed |
|----------|----------|------------|
| **A_max** | Step size | Prevents large jumps that break guarantees |
| **L_max** | First-order drift | Controls ΔV linear term |
| **H_max** | Second-order interaction | Makes curvature certificate valid |

**All three are required** for:
- Deterministic δ-bounds
- Valid ε̂ certificate (from NEC)
- Predictable scheduler behavior

Remove any one, and worst-case adversarial examples break the guarantees.

---

## Comparison Matrix

| Criterion | Option A (Implicit) | Option B (Explicit) |
|-----------|---------------------|---------------------|
| **Pre-execution verification** | ✗ No | ✓ Yes |
| **Formal safety proofs** | ✗ Limited | ✓ Full |
| **Verifier efficiency** | ✗ Requires replay | ✓ Direct check |
| **Flexibility** | ✓ High | ✗ Moderate |
| **Specification complexity** | ✓ Low | ✗ High |
| **Bounds emerge from** | Execution + invariants | Declaration + geometry |

---

## Recommendation: Option B (Explicit)

**Rationale:**

1. **Enforceable contracts**: The requirement for `A_max`, `L_max`, and Hessian bounds as enforceable contracts necessitates known bounds at verification time
2. **NEC compliance**: The curvature interaction bounds in [`5_curvature_interaction_bounds.md`](5_curvature_interaction_bounds.md) require certificate-computable bounds deterministically
3. **Verifier independence**: Explicit bounds enable the verifier to check trajectories without trusting the prover
4. **Mathematical legitimacy**: Without bounded curvature and gradient, the system is a "chaos engine with receipts" rather than a coherence engine

### Important Note on Bound Knowledge

These constants do **not** need to be known numerically at runtime.

They need to:
- **Exist** (theoretical guarantee), OR
- Be conservatively over-approximated in the M_{ij} matrix

This is a critical distinction: you don't need exact Hessians in execution, you need a safe envelope.

---

## Bound Enforcement Mechanisms

### 1. At Transition Time (Runtime)

```python
def apply_transition(x_prev, action):
    # Check operation delta bounds (A_max)
    delta = compute_delta(x_prev, action)
    assert ||delta|| ≤ A_max
    
    # Compute next state
    x_next = T(x_prev, action)
    
    # Check numeric field bounds
    assert 0 ≤ x_next.debt ≤ D_max
    assert 0 ≤ x_next.budget ≤ B_max
    
    # Check invariants
    for invariant in invariants:
        assert invariant(x_next)
    
    return x_next
```

### 2. At Verification Time (Replay)

```python
def verify_trajectory(receipts):
    x = receipts[0].state
    
    # Verify geometric bounds for each step
    for receipt in receipts[1:]:
        delta = receipt.state - receipt.prev_state
        
        # A_max: operation delta bound
        assert ||delta|| ≤ A_max
        
        # L_max: gradient bound (first-order)
        # Verified via Lipschitz condition on V
        gradient = compute_gradient_V(x)
        assert ||gradient|| ≤ L_max
        
        # H_max: curvature bound (second-order)
        # Verified via Hessian bound in neighborhood
        hessian = compute_hessian_V(receipt.neighborhood)
        assert spectral_norm(hessian) ≤ H_max
        
        x = receipt.state
```

### 3. At Contract Declaration Time

```python
def declare_contract(residual, normalizer, bounds):
    # Required bounds for enforceability
    assert bounds.A_max is not None   # Per-operation delta
    assert bounds.L_max is not None   # Gradient bound
    assert bounds.H_max is not None   # Curvature bound
    
    # Bounds must be non-negative
    assert bounds.A_max ≥ 0
    assert bounds.L_max ≥ 0
    assert bounds.H_max ≥ 0
    
    # Residual must be C² differentiable
    assert residual.is_twice_differentiable()
    
    return Contract(residual, normalizer, bounds)
```

---

## Contract Bound Specification Format

```json
{
  "contract_id": "ck0.contract.v1",
  "geometric_bounds": {
    "A_max": 1000000,
    "L_max": 1.5,
    "H_max": 1000.0
  },
  "field_bounds": {
    "debt": { "min": 0, "max": 1000000 },
    "budget": { "min": 0, "max": 500000 },
    "disturbance": { "min": 0, "max": 10000 }
  },
  "differentiability": "C2"
}
```

---

## Summary

| Element | Value |
|---------|-------|
| **ℛ definition** | Residual structure ℛ(x) = (c₁(x), ..., c_m(x)) |
| **Approach** | Explicit (Option B) |
| **A_max** | Per-operation delta bound: `\|δ_o(x)\|_X ≤ A_max(o)` |
| **L_max** | Gradient bound: `\|∇V(x)\| ≤ L_max` |
| **H_max** | Hessian bound: `\|H_V(z)\| ≤ H_max` for z in neighborhood |
| **Enforcement** | Runtime checks + verifier replay + contract declaration |

The explicit approach enables the enforceable contracts required for NEC closure and verifier independence. The key insight: without bounded curvature and gradient, the system is not a coherence engine—it's a chaos engine with receipts.
