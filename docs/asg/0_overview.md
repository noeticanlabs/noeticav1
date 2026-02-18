# ASG Overview

**Version:** 1.0  
**Status:** Draft  
**Related:** [`../nk4g/0_overview.md`](../nk4g/0_overview.md), [`../nec/0_overview.md`](../nec/0_overview.md)

---

## Mission

ASG (Adaptive Spectral Governance) provides **computable curvature models** for CK-0 residual architectures and produces spectral certificates consumed by NK-4G.

---

## What is ASG?

ASG is the **curvature layer** in the Noetica stack. It:

1. Assembles residual Jacobians O from the CK-0 residual architecture
2. Computes Hessian model H = O^T O (always PSD by construction)
3. Projects to reduced space H_⊥ = P_⊥ H P_⊥ (removes kernel)
4. Computes spectral certificates: κ₀, Γ_sem, margin M
5. Emits watchdog receipts for prox inequality verification

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ASG (v1)                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │   Types     │→ │ Operators   │→ │   Assembly          ││
│  │ (layouts)  │  │ (D, P_⊥)   │  │   (O, H = O^T O)   ││
│  └─────────────┘  └─────────────┘  └─────────────────────┘│
│         ↓                ↓                   ↓              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Spectral Analysis                           ││
│  │  κ₀ = λ_min(H_⊥),  Γ_sem,  M = Γ/κ₀                 ││
│  └─────────────────────────────────────────────────────────┘│
│         ↓                                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Watchdog (Prox Verification)              ││
│  │  V(x_{k+1}) ≤ V(z_k) - (1/2λ_k)||x_{k+1}-z_k||²    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
         ↓
   NK-4G (receipt verification)
```

---

## Layer Position

ASG sits between NEC and NK-4G:

| Layer | Role | Output |
|-------|------|--------|
| CK-0 | Residual definition | r(u), weights |
| NEC | Proximal dynamics | z_k, x_{k+1}, V values |
| **ASG** | **Spectral certificates** | **κ₀, Γ_sem, margin** |
| NK-4G | Receipt verification | Pass/Fail |

---

## Key Formulas

### State Layout

State vector: u = (ρ, θ, G, ζ) ∈ R^{4N}

| Block | Size | Description |
|-------|------|-------------|
| ρ | N | Linguistic/position |
| θ | N | Angle (mean-zero constraint) |
| G | N | Gradient |
| ζ | N | Auxiliary |

### Residual Model

Φ(u) = ½ Σ w_i |r_i(u)|²

Jacobian: O = [√w_i J_i]

Hessian: H = O^T O (always PSD by construction)

### Spectral Quantities

- κ₀ = λ_min(H_⊥) - smallest eigenvalue of projected Hessian
- v_sem = (0, G, -θ, 0) - semantic direction
- Γ_sem = (v_sem^T H_⊥ v_sem) / (v_sem^T v_sem) - semantic stiffness
- M = Γ_sem / κ₀ - semantic margin

---

## Integration with NEC

ASG certifies stability for NEC's split dynamics:

```
z_k = U_τ x_k           (drift - may increase V)
x_{k+1} = prox_{λV}(z_k)  (correction)

ASG verifies:
- H_⊥ is PSD (κ₀ > 0)
- Semantic direction is penalized (Γ_sem > 0)
- Margin is adequate (M > threshold)
```

---

## Integration with NK-4G

ASG produces receipts consumed by NK-4G:

```python
ASGReceipt {
    kappa_est: float,        # κ₀
    gamma_sem: float,        # Γ_sem  
    semantic_margin: float,  # M
    projector_id: str,       # "mean_zero_theta_v1"
    operator_digest: str,    # SHA-256 of operator structure
    estimation_method: str,  # "eigsh", "lobpcg", etc.
}
```

NK-4G verifies:
- κ₀ ≥ NK4G_KAPPA_MIN (spectral gate)
- margin ≥ NK4G_MARGIN_MIN (warning threshold)
- Receipt fields consistent

---

## Proof Obligations

| Obligation | Status |
|------------|--------|
| H = O^T O is PSD | PROVED (by construction) |
| Projection removes kernel | PROVED |
| κ₀ computable numerically | PROVED |
| κ₀ bounded below by topology | OPEN |
| Γ_sem ≥ κ₀? | OPEN |
| Massless stability (α_L=0) | EMPIRICAL |

---

## Completion Criteria

ASG v1 is complete when:
- [ ] κ₀ stable under refinement
- [ ] Margin M measurable
- [ ] NEC witness aligned
- [ ] NK-4G receipt consistent
- [ ] No document contradicts split semantics
