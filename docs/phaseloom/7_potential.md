# PhaseLoom Potential — Extended Lyapunov Functional

**Canon Doc Spine v1.0.0** — Section 8

---

## 1. Definition

### 1.1 Mathematical Formulation

Let \tilde x = (x, C, T, b, a) be the extended state. Define:

\mathcal{V}_{PL}(\tilde x) := w_0 \cdot V(x) + w_C \cdot \max(C, 0) + w_T \cdot T + w_b \cdot \psi(b) + w_a \cdot a

### 1.2 Components

| Term | Weight | Description |
|------|--------|-------------|
| V(x) | w_0 | Base CK-0 violation functional |
| max(C, 0) | w_C | Curvature penalty (only positive) |
| T | w_T | Tension accumulator |
| ψ(b) | w_b | Barrier function of budget |
| a | w_a | Authority accumulator |

---

## 2. Barrier Function

### 2.1 Canonical Choice

\psi(b) := \frac{1}{b + \epsilon}

Where \epsilon > 0 is a fixed-point constant in parameters.

### 2.2 Properties

| Property | Requirement | Status |
|----------|--------------|--------|
| Strictly decreasing | ψ'(b) < 0 | ✓ |
| Blows up at zero | lim_{b→0+} ψ(b) = ∞ | ✓ |
| Deterministic | Computable in fixed-point | ✓ |
| Bounded | lim_{b→∞} ψ(b) = 0 | ✓ |

### 2.3 Implementation

```python
def barrier(b: FixedPoint, epsilon: FixedPoint) -> FixedPoint:
    """Compute ψ(b) = 1 / (b + ε)"""
    if b + epsilon == 0:
        raise ZeroDenominatorError("b + epsilon cannot be zero")
    return FixedPoint(1) / (b + epsilon)
```

---

## 3. Weight Parameters

### 3.1 Parameter Definitions

| Weight | Type | Description |
|--------|------|-------------|
| w_0 | FixedPoint > 0 | Base violation weight |
| w_C | FixedPoint > 0 | Curvature weight |
| w_T | FixedPoint > 0 | Tension weight |
| w_b | FixedPoint > 0 | Barrier weight |
| w_a | FixedPoint > 0 | Authority weight |
| ε | FixedPoint > 0 | Barrier constant |

### 3.2 Typical Values

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| w_0 | 1.0 | Normalize to base V |
| w_C | 0.1 | Curvature penalty |
| w_T | 0.05 | Tension penalty |
| w_b | 0.01 | Budget pressure |
| w_a | 0.001 | Authority penalty |
| ε | 0.0001 | Avoid division by zero |

---

## 4. One-Step Inequality

### 4.1 Algebraic Expansion

For a transition \tilde x → \tilde x^+:

\mathcal{V}_{PL}(\tilde x^+) - \mathcal{V}_{PL}(\tilde x) =
  w_0 \Delta v 
  + w_C \max(C^+, 0) - w_C \max(C, 0)
  + w_T (T^+ - T)
  + w_b (\psi(b^+) - \psi(b))
  + w_a (a^+ - a)

### 4.2 Substitution

Using recurrences:
- C^+ = ρ_C C + (A - D)
- T^+ = ρ_T T + ΔT_inc - ΔT_res
- b^+ = b - Δb
- a^+ = a + Δa

### 4.3 Budget Charge Domination

From budget charge law: Δb ≥ κ_A A + κ_T ΔT_inc

We can bound the change in barrier:
Δψ = ψ(b - Δb) - ψ(b) ≤ -κ_A A · ψ'(b) - κ_T ΔT_inc · ψ'(b) + o(Δb)

---

## 5. Enforcement Modes

### 5.1 Weak Enforcement (v1 Recommended)

Only enforce interlock using (b) and (A):
- If b ≤ b_min: reject SOLVE with A > 0
- Don't require full V_PL on-chain

**Advantage:** Simpler, lower computation

### 5.2 Strong Enforcement

Compute and enforce V_PL ≥ Θ in STF:
- Θ: admissibility threshold
- Check at each step

**Advantage:** Full Lyapunov guarantee

---

## 6. Implementation

### 6.1 Core Computation

```python
def compute_potential(
    V: FixedPoint,      # Base violation
    C: FixedPoint,      # Curvature
    T: FixedPoint,      # Tension
    b: FixedPoint,      # Budget
    a: FixedPoint,      # Authority
    weights: Weights,
    epsilon: FixedPoint
) -> FixedPoint:
    """Compute V_PL."""
    C_penalty = max(C, FixedPoint(0))
    barrier_term = barrier(b, epsilon)
    
    return (
        weights.w0 * V +
        weights.wC * C_penalty +
        weights.wT * T +
        weights.wb * barrier_term +
        weights.wa * a
    )
```

### 6.2 State Update

```python
def update_potential(
    state: PLState,
    step: Step,
    params: PLParams
) -> FixedPoint:
    """Compute potential after step."""
    return compute_potential(
        step.v_next,
        step.C_next,
        step.T_next,
        step.b_next,
        step.a_next,
        params.weights,
        params.epsilon
    )
```

---

## 7. Relationship to Descent Theorem

### 7.1 Theorem Context

The PhaseLoom Descent Theorem (Section 10) states:
- Under repair progress conditions
- With budget charge law
- With interlock enforcement

V_PL exhibits descent outside a neighborhood of the admissible set.

### 7.2 Role of Potential

V_PL serves as the Lyapunov function that:
- Bounds the system state
- Guarantees finite escape
- Enables viability analysis

---

## 8. Receipt Integration

### 8.1 Computed Fields

| Field | Description |
|-------|-------------|
| V_PL | Computed potential value |
| V_PL_delta | Change in potential |

### 8.2 Verification

The verifier can optionally check:
- V_PL ≥ 0 (always true by construction)
- V_PL ≤ Θ (if strong mode)

---

## 9. Status

- [x] Potential definition complete
- [x] Barrier function specified
- [x] Weight parameters defined
- [x] One-step inequality derived
- [ ] Implementation in src/phaseloom/potential.py

---

*The PhaseLoom Potential V_PL is the extended Lyapunov functional that combines violation, curvature, tension, budget pressure, and authority into a single scalar for viability analysis.*
