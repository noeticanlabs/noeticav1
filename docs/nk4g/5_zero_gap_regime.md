# NK-4G Zero-Gap Regime

**Related:** [`4_spectral_analysis.md`](4_spectral_analysis.md), [`6_regularization_policy.md`](6_regularization_policy.md)

---

## 5.1 Singular Hessian

### Definition 5.1: Zero Spectral Gap

When the smallest eigenvalue of H is zero:

```
λ_min = λ_n = 0
```

This is the **zero-gap** or **singular Hessian** regime.

### Definition 5.2: Spectral Decomposition

Split the space into stable and center subspaces:

```
X = X_s ⊕ X_c
```

Where:
- **X_s**: Stable subspace spanned by eigenvectors with λ > 0
- **X_c**: Center subspace spanned by eigenvectors with λ = 0

### Dimensions

```
dim(X_s) = rank(H)
dim(X_c) = nullity(H) = n - rank(H)
```

---

## 5.2 Center Manifold Behavior

### Dynamics on Center Subspace

For vectors in X_c, the quadratic term vanishes:

```
V(x_c + d) ≈ V(x_c) + ∇V(x_c)^T d  (no quadratic term)
```

The center subspace has:
- **No local curvature** (flat direction)
- **Gradient-driven dynamics only**

### Definition 5.3: Center Manifold Update

On X_c, the discrete step reduces to:

```
x_{c,k+1} = (I + τ A) x_{c,k}
```

This is **pure resonance** - no dissipation toward minimum.

### Lemma 5.1: No Dissipation on Center

For any x_c ∈ X_c:

```
|x_{c,k+1}| = |x_{c,k}|  (norm preserved)
```

The center subspace exhibits neutrally stable behavior.

---

## 5.3 Metastability

### Definition 5.3: Metastability

When λ_min = 0 but other eigenvalues are positive:

- **Metastable**: System appears stable but can drift slowly
- **No strong convexity**: Convergence guarantees fail
- **Explicit logic drift**: NK-2 explicit steps cause drift

### Theorem 5.1: Drift Rate

On center subspace:

```
|x_{c,k}| = |(I + τ A)|^k · |x_{c,0}|
```

If A has eigenvalues ±iω:

```
|(I + τ A)| ≈ 1 + O(τ²)
```

Drift is **slow** but **persistent**.

---

## 5.4 Halting Failure Explanation

### Observation

In zero-gap regime, NK-2 may exhibit:
- **Halt without convergence**: System stops but V(x) > 0
- **Livelock-like behavior**: Continuous activity without progress
- **Explicit logic injection**: No strong convexity to drive to minimum

### NK-4G Explanation

The spectral analysis reveals:

| Condition | Explanation |
|-----------|-------------|
| λ_min = 0 | No curvature in some directions |
| Center dynamics | Neutral stability allows drift |
| Slow convergence | O(1) rate instead of exponential |
| Halting | Explicit logic exhausts budget without converging |

This is **not a bug** - it's the expected behavior when V lacks strong convexity.

---

## 5.5 Implications for Policy Design

### Avoid Zero-Gap

Policies should ensure:
- Regularization (see §6) to add artificial curvature
- Or explicitly bound nullity(H)
- Or accept metastable behavior as valid terminal state

### Detection

NK-4G can detect zero-gap:
- Monitor eigenvalue estimates from curvature matrix M
- Flag when λ_min approaches zero
- Warn that termination may be metastable

---

## 5.6 Summary

| Regime | λ_min | Behavior |
|--------|-------|----------|
| Strong convexity | λ_min > 0 | Exponential convergence |
| Weak convexity | λ_min > 0 but small | Slow convergence |
| Zero-gap | λ_min = 0 | Metastability |
| Negative | λ_min < 0 | Instability (should not occur) |

The zero-gap regime is the boundary between convergent and non-convergent behavior.
