# NK-4G Spectral Analysis

**Related:** [`3_ctd_distortion_bounds.md`](3_ctd_distortion_bounds.md), [`5_zero_gap_regime.md`](5_zero_gap_regime.md)

---

## 4.1 Quadratic Local Model

### Assumption 4.1: Local Quadratic Approximation

Assume V has a local quadratic approximation near x:

```
V(x + d) = V(x) + ∇V(x)^T d + (1/2) d^T H d + o(|d|²)
```

Where:
- `∇V` is the gradient
- `H` is the Hessian matrix
- The approximation holds in a neighborhood

### Definition 4.1: Hessian Properties

The Hessian H is:
- **Symmetric**: H = H^T (by equality of mixed partials)
- **Positive semidefinite**: λ_i ≥ 0 for all eigenvalues (coherence implies convex-like behavior locally)

### Eigenvalue Decomposition

```
H = Q Λ Q^T
```

Where:
- `Q` is orthogonal (Q^T Q = I)
- `Λ = diag(λ_1, λ_2, ..., λ_n)` with λ_i ≥ 0

---

## 4.2 Resonance Model

### Definition 4.2: Resonance Operator

Define the resonance (skew-symmetric) operator A:

```
A = S  (anti-symmetric matrix)
```

Where S represents external "forces" that cause non-dissipative behavior.

Properties:
- `A^T = -A` (skew-symmetric)
- No eigenvalues - purely imaginary spectrum

---

## 4.3 Split Scheme

### Definition 4.3: Discrete Step Operator

The discrete step combines repair (via H) and resonance (via A):

```
x_{k+1} = T_τ x_k
```

Where:

```
T_τ = (I + τ H)^{-1} (I + τ A)
```

This is a **split scheme**:
- **Implicit repair**: (I + τ H)^{-1} dissipates toward minima
- **Explicit resonance**: (I + τ A) adds rotation/drift

### Interpretation

| Component | Effect |
|-----------|--------|
| (I + τ H)^{-1} | Contraction toward coherent state |
| (I + τ A) | Resonance/rotation causing drift |

---

## 4.4 Stability Condition

### Definition 4.4: Spectral Radius

The stability of the discrete step is determined by:

```
ρ(T_τ) ≤ 1
```

Where ρ is the spectral radius (maximum absolute eigenvalue).

### Lemma 4.1: Stability Inequality

For each eigenvalue λ_i of H and imaginary eigenvalue iω_i of A:

If λ_i > 0 and ω_i > λ_i:

```
τ ≤ 2λ_i / (ω_i² - λ_i²)
```

If λ_i ≥ ω_i:

```
τ ≤ ∞  (unconditional stability)
```

### Proof Sketch

```
T_τ = (I + τ H)^{-1}(I + τ A)
    ≈ I + τ(A - H) - τ² H A  (first order)
```

Eigenvalue perturbation analysis yields the bound.

---

## 4.5 Discrete Nyquist Condition

### Theorem 4.1: Discrete Nyquist

For the split scheme:

```
|1 + iτω| / |1 + τλ| ≤ 1  for all λ ≥ 0, ω real
```

This ensures ρ(T_τ) ≤ 1.

### Equivalent Condition

```
τ ≤ 2λ / (ω² - λ²)  when ω > λ
```

This is the **discrete Nyquist condition** for stability.

---

## 4.6 Implications for NK-2

### Scheduling Implication

If batch residuals indicate high curvature:
- High ε_B → large H estimate → smaller τ needed
- Low ε_B → small H estimate → larger τ allowed

### CTD Relationship

The CTD rule Φ controls τ:
- Larger ε_B → larger τ (slower convergence, more careful)
- Smaller ε_B → smaller τ (faster convergence)

---

## 4.7 Summary

| Quantity | Definition | Role |
|----------|------------|------|
| H | Hessian of V | Local curvature |
| A | Resonance operator | External drift |
| τ | Step size | CTD-controlled |
| λ_i | Eigenvalues of H | Curvature magnitudes |
| ω_i | Imaginary eigenvalues of A | Resonance frequencies |
| ρ(T_τ) | Spectral radius | Stability measure |
