# NK-4G Metric Structure

**Related:** [`0_overview.md`](0_overview.md), [`2_curvature_definition.md`](2_curvature_definition.md)

---

## 1.1 State Space

Let **X** denote the state space as defined in NK-1 §1.5 under canonical numeric embedding.

Only numeric fields with `participates_in_delta_norm=true` define coordinates in the metric space.

Non-numeric fields (identifiers, blobs, references) are excluded from the metric structure.

### Definition 1.1: Numeric Embedding

For a state `x`, let `emb(x)` denote the vector of numeric field values in canonical ordering:

```
emb(x) = [f_1, f_2, ..., f_n] where f_i ∈ ℤ (quantized)
```

The embedding preserves ordering but does not imply any topology on the original state space.

---

## 1.2 Fixed Diagonal Metric

### Definition 1.2: Weight Vector

Define weights `w_k > 0` from PolicyBundle schema:

```
w = [w_1, w_2, ..., w_n] where w_k ∈ ℕ (positive integers)
```

Weights are:

- **Static**: Determined at PolicyBundle creation, never change during execution
- **Policy-locked**: Hash-bound in PolicyBundle
- **Deterministic**: Same weights for all executions with same PolicyBundle

### Definition 1.3: Inner Product and Norm

Given weight vector `w`, define:

```
⟨u, v⟩_G = Σ_k w_k · u_k · v_k

|u|_G² = Σ_k w_k · u_k²
```

This is a **diagonal weighted inner product** with metric matrix `G = diag(w)`.

### Lemma 1.1: Norm Equivalence

For any vectors `u, v`:

```
|u|_G² = u^T G u
```

The G-norm satisfies:

```
min(w) · |u|₂² ≤ |u|_G² ≤ max(w) · |u|₂²
```

---

## 1.3 Constraints

### No State-Dependent Weights

**v1.0 Rule**: Weights `w_k` must be constants, not functions of state.

This ensures:

- Determinism across executions
- No implicit degrees of freedom
- Receipt reproducibility

### Integer-Backed Weights

Weights are stored as integers (DebtUnit scale) to maintain exact arithmetic:

```
w_k ∈ ℕ, w_k ≥ 1
```

---

## 1.4 Relationship to NK-1

| NK-1 Quantity | NK-4G Interpretation |
|---------------|---------------------|
| δ_g(x) | Displacement vector in (X, ⟨·,·⟩_G) |
| ε_B | Batch residual as G-norm difference |
| σ_k | Per-contract weight bound |
| V(x) | Coherence functional (not norm) |

The metric structure provides the geometric interpretation layer. NK-1 computations remain unchanged.

---

## 1.5 Canonical Ordering

Fields are ordered by:

1. Field ID bytes (lexicographic)
2. Weight vector follows this same ordering
3. Matrix entries (curvature) follow this ordering

This ensures deterministic metric construction.
