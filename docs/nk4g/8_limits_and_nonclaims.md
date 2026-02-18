# NK-4G Limits and Non-Claims

**Related:** [`7_verifier_consistency.md`](7_verifier_consistency.md), [`9_formalization_plan.md`](9_formalization_plan.md)

---

## 8.1 Explicit Non-Claims

NK-4G provides geometric and spectral interpretation. It does **not** claim:

### Geometry

| Non-Claim | Description |
|-----------|-------------|
| Continuous manifold geometry | X is a discrete state space, not a manifold |
| Riemannian structure | No metric tensor, only diagonal weights |
| Geodesics | No path optimization interpretation |
| Tangent spaces | No differential structure |

### Physics

| Non-Claim | Description |
|-----------|-------------|
| GR equivalence | Not related to general relativity |
| Quantum interpretation | No wave functions or operators |
| Thermodynamics | Entropy not defined |
| Physical units | No SI unit interpretation |

### Convergence

| Non-Claim | Description |
|-----------|-------------|
| Global convergence | Only local quadratic model |
| Rate guarantees | Without strong convexity |
| Optimality | Not a gradient descent method |
| Landscape analysis | No global minima finding |

---

## 8.2 Assumptions Required

NK-4G analysis relies on assumptions that must hold:

### Assumption Summary

| Assumption | Description | Required For |
|------------|-------------|--------------|
| A4.1 | Local quadratic approximation | Spectral analysis |
| A4.2 | Symmetric positive semidefinite H | Eigenvalue decomposition |
| A3.1 | Lipschitz CTD function | Distortion bounds |
| A5.1 | λ_min ≥ 0 (not negative) | Stability |

### When Assumptions Fail

| If... | Then... |
|-------|---------|
| Quadratic model fails | Spectral analysis invalid |
| H has negative eigenvalues | Instability (system bug) |
| CTD not Lipschitz | Distortion bounds fail |
| λ_min < 0 | Contract violation (should not occur) |

---

## 8.3 Limits of Interpretation

### Local Only

The quadratic model is **local**:
- Valid only near current state x
- May not hold for large displacements
- Curvature may change with x

### Discrete, Not Continuous

NK-4G interprets **discrete** quantities:
- δ_g is finite difference, not derivative
- ε_B is discrete curvature, not Hessian
- No limit processes assumed

### Approximate

Spectral analysis is **approximate**:
- M is discrete curvature, not exact Hessian
- Eigenvalue estimates from M may be loose
- Stability conditions are sufficient, not necessary

---

## 8.4 What NK-4G Does NOT Guarantee

### Correctness

- Does NOT guarantee contract satisfaction (NK-1 does)
- Does NOT guarantee termination (NK-2 does)
- Does NOT guarantee resource bounds (NK-2 does)

### Performance

- Does NOT provide optimal scheduling
- Does NOT minimize any objective
- Does NOT predict convergence rate

### Security

- Does NOT provide additional guarantees
- Does NOT affect replay verification
- Does NOT add safety properties

---

## 8.5 Use Cases

### Appropriate Use

NK-4G IS appropriate for:

| Use Case | Description |
|----------|-------------|
| Understanding | Why is convergence slow? |
| Diagnosis | Why did halt occur? |
| Governance | Monitoring spectral gap |
| Policy design | Setting ε regularization |
| Debugging | Interpreting execution traces |

### Inappropriate Use

NK-4G is NOT appropriate for:

| Use Case | Why Not |
|----------|---------|
| Proving termination | Use NK-2 proofs |
| Verifying contracts | Use NK-1 verifier |
| Optimizing execution | Use NK-2 scheduler |
| Guaranteeing resources | Use NK-2 caps |

---

## 8.6 Summary

NK-4G provides:

- **Interpretation**: Geometric meaning of existing quantities
- **Analysis**: Spectral properties of V landscape
- **Guidance**: Policy decisions for regularization
- **Diagnostics**: Understanding execution behavior

NK-4G does NOT provide:

- **New guarantees**: All contracts from NK-1/2/3
- **New verification**: All verification from NK-1
- **New correctness**: Core semantics unchanged

Use NK-4G to **understand** the system, not to **fix** the system.
