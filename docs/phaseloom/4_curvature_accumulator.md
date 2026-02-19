# PhaseLoom Curvature Accumulator

**Canon Doc Spine v1.0.0** — Section 5

---

## 1. Per-Step Amp/Diss Definitions

### 1.1 Violation Delta

For a transition (x \to x^+):
- (v = V(x)): Current violation value
- (v^+ = V(x^+)): Next violation value
- (\Delta v = v^+ - v): Violation change

### 1.2 Amplification

A = (\Delta v)_+ = \max(\Delta v, 0)

- **Interpretation:** Positive violation change (worsening)
- **Type:** Non-negative scalar
- **Synonyms:** "amp", "amplification"

### 1.3 Dissipation

D = (-\Delta v)_+ = \max(-\Delta v, 0)

- **Interpretation:** Negative violation change (improvement)
- **Type:** Non-negative scalar
- **Synonyms:** "diss", "dissipation"

### 1.4 Properties

| Property | Value |
|----------|-------|
| A \cdot D = 0 | Amp and diss are mutually exclusive |
| \Delta v = A - D | Decomposition |
| A, D \in \mathbb R_{\ge 0} | Non-negative |

---

## 2. Canonical Curvature Recurrence

### 2.1 Exponential Window Formula

C^+ := \rho_C \cdot C + (A - D)

Where:
- (C): Current curvature
- (C^+): Next curvature
- (\rho_C \in [0, 1)): Decay factor
- (A): Amplification
- (D): Dissipation

### 2.2 Clamping

After computing C^+, store:
C_+ := \max(C, 0)

This ensures curvature penalty is always non-negative.

### 2.3 Implementation

```python
def compute_curvature_next(
    C: FixedPoint,
    A: FixedPoint,
    D: FixedPoint,
    rho_C: FixedPoint
) -> FixedPoint:
    """Compute C^+ = rho_C * C + (A - D)"""
    raw = rho_C * C + (A - D)
    return max(raw, FixedPoint(0))  # C_+
```

---

## 3. Interpretation

### 3.1 Curvature States

| Curvature Value | Interpretation |
|-----------------|----------------|
| (C > 0) | Net amplification dominating dissipation over the effective window |
| (C = 0) | Balanced amp/diss or no history |
| (C < 0) | Net dissipation dominating (clamped to 0 in v1) |

### 3.2 Effective Window

The exponential decay (\rho_C) defines an effective window:
- (\rho_C = 0.9): ~10 steps for 67% contribution
- (\rho_C = 0.99): ~100 steps for 67% contribution

### 3.3 Geometric Interpretation

Curvature tracks the "acceleration" of violation:
- Positive curvature: Violation trending upward
- Negative curvature: Violation trending downward
- Zero curvature: Neutral or balanced

---

## 4. Determinism Requirements

### 4.1 Fixed-Point Arithmetic

All curvature computations use fixed-point arithmetic:
- Multiplication: `mul_fix(a, b)` with truncation toward zero
- Addition/Subtraction: Exact integer operations

### 4.2 Representation

| Parameter | Representation |
|-----------|----------------|
| C | Fixed-point (scaled by 10^6) |
| \rho_C | Fixed-point rational in [0, 1) |
| A | Fixed-point (from V delta) |
| D | Fixed-point (from V delta) |

### 4.3 Non-Determinism Prevention

- **No float:** All computations in integer fixed-point
- **No random:** No stochastic operations
- **No external:** No system time dependencies

---

## 5. Budget Charge Integration

### 5.1 Amplification Cost

Curvature directly affects budget through the budget charge law:

\Delta b \ge \kappa_A \cdot A + \kappa_T \cdot \Delta T_{inc}

Where (\kappa_A > 0) is the amplification budget price.

### 5.2 Cost Implications

- High (A) → High budget charge
- High curvature (C) → Indicates sustained amplification → Budget pressure

---

## 6. Receipt Fields

### 6.1 Required Fields

| Field | Description |
|-------|-------------|
| C_prev | Curvature before step |
| C_next | Curvature after step |
| A | Amplification |
| D | Dissipation |
| rho_C | Decay factor used |

### 6.2 Verification

The verifier checks:
1. Compute A, D from v_prev, v_next
2. Verify C_next = rho_C * C_prev + (A - D)
3. Verify C_next >= 0 (clamping)

---

## 7. Example Traces

### 7.1 Improving Trajectory

| Step | v | v^+ | Δv | A | D | C_prev | C^+ |
|------|---|-----|-----|---|---|--------|-----|
| 0 | 1.0 | - | - | - | - | 0 | 0 |
| 1 | 1.0 | 0.8 | -0.2 | 0 | 0.2 | 0 | -0.2 → 0 |
| 2 | 0.8 | 0.5 | -0.3 | 0 | 0.3 | 0 | -0.3 → 0 |

### 7.2 Degrading Trajectory

| Step | v | v^+ | Δv | A | D | C_prev | C^+ |
|------|---|-----|-----|---|---|--------|-----|
| 0 | 1.0 | - | - | - | - | 0 | 0 |
| 1 | 1.0 | 1.2 | +0.2 | 0.2 | 0 | 0 | 0.2 |
| 2 | 1.2 | 1.5 | +0.3 | 0.3 | 0 | 0.2 | 0.5 |

---

## 8. Status

- [x] Amp/diss definitions complete
- [x] Curvature recurrence specified
- [x] Clamping rule defined
- [x] Determinism requirements stated
- [ ] Implementation in src/phaseloom/curvature.py

---

*The curvature accumulator C tracks the net amplification over dissipation, enabling geometric bounds on violation dynamics.*
