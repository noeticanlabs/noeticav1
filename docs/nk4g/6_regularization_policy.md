# NK-4G Regularization Policy

**Related:** [`5_zero_gap_regime.md`](5_zero_gap_regime.md), [`7_verifier_consistency.md`](7_verifier_consistency.md)

---

## 6.1 Artificial Viscosity

### Definition 6.1: Regularized Coherence Functional

When spectral gap vanishes (λ_min = 0), introduce regularization:

```
V_ε(x) = V(x) + (ε/2) · |x|_G²
```

Where:
- `ε > 0` is the regularization parameter
- `|x|_G²` is the G-norm from §1.2
- V_ε is the regularized functional

### Lemma 6.1: Curvature Restoration

The regularized Hessian:

```
H_ε = H + εI
```

Has eigenvalues:

```
λ_i(H_ε) = λ_i(H) + ε
```

Therefore:

```
λ_min(H_ε) ≥ ε > 0
```

Spectral gap is restored.

---

## 6.2 Bias Declaration

### Requirement: Explicit Bias Declaration

When regularization is applied, it must be **declared**:

| Field | Description |
|-------|-------------|
| `regularization_enabled` | Boolean flag |
| `epsilon_value` | The ε parameter |
| `epsilon_policy_id` | Policy that defines ε |
| `bias_justification` | Why regularization is needed |

### Policy Binding

The regularization parameter ε is bound in PolicyBundle:

```
PolicyBundle.regularization_epsilon = ε
PolicyBundle.regularization_policy_id = "<policy>"
```

---

## 6.3 Compiler Enforcement

### Role of NK-3 Compiler

The compiler (NK-3) may:

1. **Detect flat directions**: Identify when curvature matrix M suggests λ_min ≈ 0
2. **Require regularization**: Reject PolicyBundle without valid ε when flat directions detected
3. **Bind ε in PolicyBundle**: Ensure ε is hash-locked before execution

### Detection Algorithm

```
if min_eigenvalue_estimate(M) < ε_threshold:
    require regularization
    require ε >= ε_min
```

---

## 6.4 Trade-offs

### Benefits of Regularization

| Benefit | Description |
|---------|-------------|
| Strong convexity | λ_min ≥ ε ensures exponential convergence |
| Stability | Spectral gap prevents metastability |
| Termination | Guaranteed progress toward minimum |

### Costs of Regularization

| Cost | Description |
|------|-------------|
| Bias | Solution biased toward origin (small x) |
| Over-regularization | Large ε distorts original V |
| Policy lock | ε cannot change during execution |

---

## 6.5 Selection Guidelines

### When to Regularize

| Condition | Recommendation |
|-----------|----------------|
| Zero-gap detected | Require ε ≥ ε_min |
| Metastable halt | Could retry with regularization |
| High-dimensional nullity | Require stronger regularization |
| Real-time constraints | Use small ε for speed |

### ε Selection

| Regime | Suggested ε |
|--------|-------------|
| Near-zero gap | ε = 1e-6 · V_scale |
| Moderate flatness | ε = 1e-4 · V_scale |
| Strong regularization | ε = 1e-2 · V_scale |

V_scale is the typical V(x) magnitude (DebtUnit).

---

## 6.6 Implementation

### V_ε Computation

```
def V_epsilon(x, epsilon):
    V_x = V(x)                         # Original NK-1 V
    norm_sq = sum(w_k * x_k^2)          # G-norm squared
    return V_x + (epsilon * norm_sq) // 2
```

All computation in DebtUnit integers.

### Gradient Modification

The regularized gradient:

```
∇V_ε(x) = ∇V(x) + ε · G · x
```

Where G is the diagonal weight matrix.

---

## 6.7 Summary

| Aspect | Requirement |
|--------|-------------|
| Enable | Via PolicyBundle flag |
| Parameter | ε > 0 bound in PolicyBundle |
| Detection | NK-3 analyzes curvature matrix M |
| Bias | Must be declared in receipts |
| Removal | NK-4G can be removed; receipts unchanged |

Regularization is a **policy choice**, not a requirement. The system can operate without it but may experience metastability.
