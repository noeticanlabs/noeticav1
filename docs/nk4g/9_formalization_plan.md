# NK-4G Formalization Plan

**Related:** [`8_limits_and_nonclaims.md`](8_limits_and_nonclaims.md), [`0_overview.md`](0_overview.md)

---

## 9.1 Lean Formalization Goals

This document outlines milestones for formalizing NK-4G in Lean. The goal is machine-checked proofs of key theorems, not full verification of NK-1/NK-2.

### Scope

- Core geometric definitions
- Spectral lemmas
- Stability bounds
- NOT: Full NK-1/NK-2 verification (separate effort)

### Dependencies

- Linear algebra library (matrix, eigenvalues)
- Real analysis (norms, limits)
- Basic topology (metric spaces)

---

## 9.2 Milestone 1: Finite Dimensional Spectral Lemma

### Goal

Prove eigenvalue bounds for symmetric matrices.

### Statement

```
∀ (H : Matrix n n ℝ), H = H^T → 
  ∀ i, λ_i(H) ∈ ℝ ∧ |λ_i(H)| ≤ ‖H‖_Fro
```

### Files

```
nk4g/spectral/basic.lean
nk4g/spectral/eigenvalue_bounds.lean
```

### Dependencies

- Matrix.transpose_eq
- Matrix.mul_vec
- NormedSpace.l2_inner

---

## 9.3 Milestone 2: Proximal Descent Theorem

### Goal

Prove that proximal operator decreases objective.

### Statement

```
∀ (f : ℝ^n → ℝ) (convex, differentiable),
∀ (x : ℝ^n) (γ > 0),
  f(prox_γ(x)) ≤ f(x) - (γ/2) ‖∇f(x)‖²
```

### Files

```
nk4g/proximal/basic.lean
nk4g/proximal/descent.lean
```

### Dependencies

- Convexity definition
- Gradient properties
- Norm inequalities

---

## 9.4 Milestone 3: Lipschitz CTD Distortion Bound

### Goal

Prove Lemma 3.1 from document.

### Statement

```
∀ (Φ : ℝ × ℝ → ℝ), 
  (∀ x y, |Φ(x,y) - Φ(x,0)| ≤ L * |y|) →
∀ (V : ℝ) (ε : ℝ),
  |Φ(V,ε)| ≤ L * |ε|
```

### Files

```
nk4g/ctd/lipschitz.lean
nk4g/ctd/bounds.lean
```

### Dependencies

- Milestone 1 (norms)
- Lipschitz definition

---

## 9.5 Milestone 4: Telescoping Inequality

### Goal

Prove Theorem 3.1 - accumulated distortion bound.

### Statement

```
∀ (T : ℕ) (ε : ℕ → ℝ) (L : ℝ),
  (∀ t, |δ_t| ≤ L * ε_t) →
  |Σ_{t=1}^T δ_t| ≤ L * Σ_{t=1}^T ε_t
```

### Files

```
nk4g/ctd/telescoping.lean
```

### Dependencies

- Milestone 3
- Sum inequalities

---

## 9.6 Milestone 5: Spectral Stability Bound (Quadratic Case)

### Goal

Prove Theorem 4.1 - stability of split scheme.

### Statement

```
∀ (H : Matrix n n ℝ) (symmetric, H ≥ 0),
∀ (A : Matrix n n ℝ) (skew: A^T = -A),
∀ (τ : ℝ) (τ > 0),
  spectral_radius((I + τH)⁻¹ (I + τA)) ≤ 1
```

### Files

```
nk4g/spectral/stability.lean
nk4g/spectral/split_scheme.lean
```

### Dependencies

- Milestone 1 (eigenvalues)
- Matrix inverse
- Spectral radius definition

---

## 9.7 Implementation Order

| Milestone | Est. Complexity | Dependencies |
|-----------|-----------------|--------------|
| 1 | Medium | Basic linear algebra |
| 2 | Medium | Convex analysis |
| 3 | Low | Milestone 1 |
| 4 | Low | Milestone 3 |
| 5 | High | Milestone 1, matrix theory |

---

## 9.8 Formalization Notes

### Integer vs Real

NK-4G formalization works in ℝ for analysis. The discrete integer implementation in NK-1 is separate.

### Key Abstraction Gap

| Document | Formalization |
|----------|---------------|
| δ_g ∈ ℤ^n | δ_g ∈ ℝ^n (for analysis) |
| V(x) ∈ DebtUnit | V(x) ∈ ℝ (for analysis) |
| ε_B ∈ DebtUnit | ε_B ∈ ℝ (for analysis) |

The abstraction gap must be bridged by:
1. Showing DebtUnit integers embed in ℝ
2. Showing bounds transfer

### Strategy

```
1. Formalize in ℝ (easier)
2. Show integer variant satisfies same bounds
3. Use for analysis, not verification
```

---

## 9.9 Resources

### Lean Libraries Needed

- `mathlib` (standard)
- `analysis` (normed spaces)
- `linear_algebra` (eigenvalues)

### Estimated Effort

Not estimated - focus on milestones, not timelines.

---

## 9.10 Summary

| Milestone | Theorem | File |
|-----------|---------|------|
| 1 | Eigenvalue bounds | spectral/basic |
| 2 | Proximal descent | proximal/descent |
| 3 | Lipschitz CTD | ctd/lipschitz |
| 4 | Telescoping | ctd/telescoping |
| 5 | Spectral stability | spectral/stability |

All formalization does NOT affect runtime. It provides mathematical confidence in the interpretation layer.
