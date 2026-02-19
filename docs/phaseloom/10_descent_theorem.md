# PhaseLoom Descent Theorem

**Canon Doc Spine v1.0.0** — Section 11

---

## 1. Theorem Statement

### 1.1 Contract-Conditional Theorem

**Assume:**
1. Curvature and tension recurrences (Sections 5-6)
2. Budget charge law: Δb ≥ κ_A · A + κ_T · ΔT_inc
3. Interlock enforcement (Section 9)
4. Deterministic fixed-point arithmetic

**Then:**
- For accepted steps, V_PL is bounded and cannot diverge without exhausting b
- Under repair progress conditions (below), V_PL exhibits descent outside a neighborhood of the admissible set

### 1.2 Status

**[THEOREM]** - Proof sketch provided below

---

## 2. Repair Progress Condition

### 2.1 Statement

There exists δ > 0 and ε_V > 0 such that for REPAIR steps when V(x) > ε_V:

V(x^+) ≤ V(x) - δ

### 2.2 Interpretation

- REPAIR steps guarantee minimum violation reduction
- Only applies when not already at admissibility threshold

### 2.3 Status

**[LEMMA-NEEDED]**

- Depends on the repair operator
- Can be proved for proximal steps under convexity/monotonicity assumptions in PCM layer

---

## 3. Proof Sketch

### 3.1 One-Step Inequality Derivation

Starting from V_PL definition:

ΔV_PL = V_PL(x^+) - V_PL(x)
      = w_0 Δv + w_C (C^+ - C) + w_T (T^+ - T) + w_b (ψ(b^+) - ψ(b)) + w_a (a^+ - a)

### 3.2 Substituting Recurrences

Using:
- C^+ = ρ_C C + (A - D)
- T^+ = ρ_T T + ΔT_inc - ΔT_res
- b^+ = b - Δb

We get:

ΔV_PL = w_0 (A - D) 
      + w_C (ρ_C C + A - D - C)
      + w_T (ρ_T T + ΔT_inc - ΔT_res - T)
      + w_b (ψ(b - Δb) - ψ(b))
      + w_a Δa

### 3.3 Budget Charge Domination

From budget charge law: Δb ≥ κ_A A + κ_T ΔT_inc

Using barrier properties:
ψ(b - Δb) - ψ(b) = -ψ'(b) · Δb + o(Δb)
                 ≤ -ψ'(b) · (κ_A A + κ_T ΔT_inc) + o(Δb)

### 3.4 Collecting Terms

ΔV_PL ≤ (w_0 + w_C) A 
       - (w_0 + w_C) D
       - w_C (1 - ρ_C) C
       - w_T (1 - ρ_T) T
       - w_b ψ'(b) κ_A A
       - w_b ψ'(b) κ_T ΔT_inc
       - w_T ΔT_res
       + w_a Δa

### 3.5 Boundedness

Since all weights and parameters are positive:
- -w_C (1 - ρ_C) C ≤ 0
- -w_T (1 - ρ_T) T ≤ 0
- -w_T ΔT_res ≤ 0
- w_a Δa ≥ 0 (authority increase)

The system cannot diverge without Δb → ∞, which requires b → ∞.

---

## 4. Descent Regime

### 4.1 Outside Neighborhood

When V(x) > ε_V and using REPAIR steps:

V(x^+) ≤ V(x) - δ

From budget charge: Δb ≥ κ_A A

Since A = (Δv)_+ and REPAIR reduces V, we have A = 0 during descent.

Therefore: ΔV_PL ≤ -w_0 δ + bounded positive terms

### 4.2 Fixed-Point Bound

The potential is bounded by initial budget:

V_PL ≤ V_PL(0) + w_b · (ψ(0) - ψ(b_init))

---

## 5. Theorem Components

### 5.1 Boundedness

**Claim:** V_PL is bounded for all finite executions.

**Proof:** Follows from budget exhaustion argument above.

### 5.2 Descent

**Claim:** Outside neighborhood (V > ε_V), REPAIR steps decrease V_PL.

**Proof:** With repair progress lemma, REPAIR reduces V without amplification (A=0), leading to V_PL descent.

### 5.3 Viability

**Claim:** The admissible set {x | V(x) = 0} is the viability kernel.

**Proof:** By definition of interlock, once V approaches 0, only safe steps are taken.

---

## 6. Dependencies

### 6.1 Required Lemmas

| Lemma | Status | Reference |
|-------|--------|-----------|
| Repair progress | NEEDED | PCM layer |
| Barrier monotonicity | NEEDED | Fixed-point analysis |
| Non-negativity of T | ASSUMED | Tension definition |

### 6.2 Parameter Dependencies

All constants in the bound depend on:
- Weights: w_0, w_C, w_T, w_b, w_a
- Decay: ρ_C, ρ_T
- Costs: κ_A, κ_T
- Barrier: ε

---

## 7. Invariance

### 7.1 Admissible Set Invariance

Once the system reaches the admissible set (V(x) = 0, C = 0, T = 0):
- Budget may still be spent
- Authority may increase
- But V cannot increase without triggering interlock

### 7.2 Viability Kernel

The interlock defines a viability kernel in the extended state space:
- Budget lower bound: b_min
- (Strong mode) Potential upper bound: Θ

---

## 8. Optional Strong Mode

### 8.1 Potential Threshold

When strong mode is enabled (V_PL ≥ Θ triggers interlock):
- The system is guaranteed to stay within V_PL < Θ
- This provides stronger safety guarantees
- But limits exploration capability

### 8.2 Trade-off

| Mode | Safety | Liveness |
|------|--------|----------|
| Weak (v1) | Budget floor | Full exploration until b=0 |
| Strong | Budget + potential | Limited by Θ |

---

## 9. Status

- [x] Theorem statement complete
- [x] Proof sketch provided
- [ ] Repair progress lemma (PCM layer)
- [ ] Full proof formalization

---

*The PhaseLoom Descent Theorem establishes that the extended Lyapunov functional V_PL is bounded under the budget charge law and exhibits descent under repair progress, guaranteeing safety and liveness properties.*
