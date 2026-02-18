# NK-4G Curvature Definition

**Related:** [`1_metric_structure.md`](1_metric_structure.md), [`3_ctd_distortion_bounds.md`](3_ctd_distortion_bounds.md)

---

## 2.1 Single-Op Displacement

### Definition 2.1: Operator Displacement

For an operator `g`, define the displacement:

```
δ_g(x) = emb(x_g) - emb(x)
```

Where:
- `x_g` is the state after applying operator `g`
- `emb` is the numeric embedding from §1.1
- `δ_g(x) ∈ ℤ^n` is an integer vector

### Lemma 2.1: Displacement Norm Bound

The norm of displacement under G-metric is:

```
|δ_g(x)|_G² = Σ_k w_k · (δ_g(x)_k)²
```

NK-1 enforces exact integer inequality:

```
|δ_g(x)|_G² ≤ bound_g
```

This is a **hard constraint** from NK-1, not an approximation.

---

## 2.2 Mixed Residual (Discrete Curvature)

### Definition 2.2: Mixed Residual

For two operators `g` and `h`, define the mixed residual:

```
ε_gh(x) = V(x + δ_g + δ_h) - V(x + δ_g) - V(x + δ_h) + V(x)
```

This is a **discrete mixed second difference**, measuring non-additivity of V across operator pairs.

### Interpretation

| Case | ε_gh Interpretation |
|------|---------------------|
| ε_gh = 0 | Additive (linear) |
| ε_gh > 0 | Convex-like behavior |
| ε_gh < 0 | Concave-like behavior |

This is NOT continuous curvature (which requires Hessian). It is a **discrete curvature measure** computable from V values alone.

### Lemma 2.2: Batch Mixed Residual

For a batch `B = {g₁, g₂, ..., g_m}`:

```
ε_B = V(x + Σ_{g∈B} δ_g) - Σ_{g∈B} V(x + δ_g) + (m-1)·V(x)
```

This extends to arbitrary batch size.

---

## 2.3 Batch Residual

### Definition 2.3: Batch Residual

For a batch `B`, the batch residual is:

```
ε_B = ΔV_B - Σ_{g∈B} ΔV_g
```

Where:
- `ΔV_B = V(x_after_batch) - V(x_before)`
- `ΔV_g = V(x_after_g) - V(x_before_g)`

This is already defined in NK-1 §1.6. NK-4G provides geometric interpretation.

### Lemma 2.3: Relation to Mixed Residuals

For batch `B = {g, h}`:

```
ε_{g,h} = ε_B
```

For larger batches, ε_B aggregates multiple mixed residuals.

---

## 2.4 Curvature Matrix Interpretation

### Definition 2.4: Discrete Curvature Matrix

Define matrix `M` (NEC closure matrix from NK-1) as:

```
M_{ij} = ε_{g_i, g_j}(x) for operator pair (i, j)
```

The curvature matrix `M` is:
- **Symmetric**: ε_gh = ε_hg
- **Diagonal zero**: ε_gg = 0
- **State-dependent**: Changes with x

### Relationship to Continuous Curvature

If V is twice-differentiable near x:

```
M ≈ (1/2) · H(x)  (H = Hessian)
```

But NK-4G makes **no continuity assumption**. The discrete M is the primary object.

---

## 2.5 Bounds from NEC Closure

### Lemma 2.5: Curvature Bound

From NK-1 NEC closure:

```
|ε_gh(x)| ≤ C_ε  for all g, h, x in reachable region ℛ
```

The bound `C_ε` is policy-locked in PolicyBundle.

---

## 2.6 Summary

| Quantity | Definition | Type |
|----------|------------|------|
| δ_g(x) | emb(x_g) - emb(x) | Vector |
| ε_gh(x) | V(x+δ_g+δ_h) - V(x+δ_g) - V(x+δ_h) + V(x) | Scalar |
| ε_B | V(x+Σδ) - ΣV(x+δ) + (|B|-1)V(x) | Scalar |
| M_{ij} | ε_{g_i,g_j} | Matrix |
