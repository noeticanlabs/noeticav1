# NEC Soundness Theorems

**Related:** [`8_compositionality.md`](8_compositionality.md), [`10_limits.md`](10_limits.md)

---

## 9.1 Theorem 1: Per-Step Descent

### Statement

If the ProxWitness inequality holds:

```
V(x_{k+1}) ≤ V(x_k) - (1/(2·τ·g_k)) · |x_{k+1} - y_k|_G²
```

Then:

```
V(x_{k+1}) ≤ V(x_k)
```

### Proof

Since |x_{k+1} - y_k|_G² ≥ 0 and τ > 0, g_k > 0:

```
-(1/(2·τ·g_k)) · |x_{k+1} - y_k|_G² ≤ 0
```

Therefore:

```
V(x_{k+1}) ≤ V(x_k) + 0 = V(x_k)
```

∎

### Implication

V never increases across steps. Execution is monotone non-increasing in V.

---

## 9.2 Theorem 2: Finite Energy Bound

### Statement

Summing the witness inequality over k = 0 to T-1:

```
Σ_{k=0}^{T-1} (1/(2·τ_k·g_k)) · |x_{k+1} - y_k|_G² ≤ V(x_0) - V(x_T)
```

Since V(x_T) ≥ 0:

```
Σ_{k=0}^{T-1} (1/(2·τ_k·g_k)) · |x_{k+1} - y_k|_G² ≤ V(x_0)
```

### Proof

Telescoping sum:

```
Σ (V(x_k) - V(x_{k+1})) = V(x_0) - V(x_T)
```

By Theorem 1, each term V(x_k) - V(x_{k+1}) ≥ the witness term.

Rearranging gives the bound.

∎

### Implication

Total "movement energy" is bounded by initial V. Execution terminates or V reaches 0.

---

## 9.3 Theorem 3: Fejér Monotonicity

### Statement

The sequence {x_k} is Fejér monotone with respect to any fixed point x*:

```
|x_{k+1} - x*|_G ≤ |x_k - x*|_G
```

### Proof Sketch

Let y_k be the proximal point. For convex V:

```
|y_k - x*|_G ≤ |x_k - x*|_G
```

And since x_{k+1} is obtained by moving from y_k in a descent direction:

```
|x_{k+1} - x*|_G ≤ |y_k - x*|_G ≤ |x_k - x*|_G
```

∎

### Implication

The sequence remains bounded and does not diverge. No explosion.

---

## 9.4 Theorem 4: Gate Soundness

### Statement

If gate(x, B) passes:

```
|ε_B| ≤ ε̂_B = Σ_{i<j} |M_{ij}| · a_i · a_j
```

Then the multi-operator execution preserves bounded descent structure:

```
There exists τ > 0 such that:
V(x') ≤ V(x) - (1/(2·τ)) · |x' - y|_G²
```

Where x' = patch(x, B).

### Proof Sketch

1. From gate passing: |ε_B| ≤ ε̂_B
2. From curvature bound: ε̂_B = Σ_{i<j} |M_{ij}| · a_i · a_j
3. From operator bounds: |δ_o(x)|_G ≤ a_o for all o ∈ B
4. Combine to get: |ε_B| ≤ C · Σ a_o² for some constant C
5. Choose τ small enough: τ ≤ 1/(2C)
6. Then witness inequality holds

∎

### Implication

Gate passing is sufficient for descent. Safe batches guarantee progress.

---

## 9.5 Theorem 5: Termination

### Statement

If all batches pass the gate and V is bounded below:

```
lim_{k→∞} V(x_k) = V* ≥ 0
```

And the execution terminates in finite steps.

### Proof Sketch

From Theorem 2:

```
Σ |x_{k+1} - y_k|_G² ≤ 2 · V(x_0) · max(τ_k·g_k) < ∞
```

The infinite sum of movement terms is finite.

If V has minimum V* ≥ 0, then eventually V(x_k) = V* and movement stops.

∎

### Implication

With bounded V and passing gates, execution terminates.

---

## 9.6 Theorem 6: Receipt Verifiability

### Statement

If a receipt passes verification:

```
V(x_{k+1}) ≤ V(x_k) - (1/(2·τ·g)) · |x_{k+1} - y|_G²
```

Then the execution followed NEC rules.

### Proof Sketch

The witness inequality requires:
1. Valid state transitions (checked by hash)
2. Gate passed (witness would fail otherwise)
3. Proper V computation (checked)
4. Proper proximal point (inequality would fail)

If all hold, execution was NEC-compliant.

∎

### Implication

Receipts are sufficient to verify NEC compliance.

---

## 9.7 Summary Table

| Theorem | Property | Mathematical Form |
|---------|----------|-------------------|
| 1 | Per-step descent | V(x_{k+1}) ≤ V(x_k) |
| 2 | Finite energy | Σ movement ≤ V(x_0) |
| 3 | Fejér monotone | \|x_{k+1}-x*\| ≤ \|x_k-x*\| |
| 4 | Gate soundness | pass ⇒ descent possible |
| 5 | Termination | Σ bounded ⇒ finite steps |
| 6 | Receipt verifiability | witness ⇒ NEC compliance |

---

## 9.8 Assumptions

Theorems require:

| Assumption | Description |
|------------|-------------|
| A1 | V : X → ℝ_{\ge 0} |
| A2 | Gate passes for all batches |
| A3 | τ_k > 0 bounded |
| A4 | g_k > 0 bounded |
| A5 | Operator bounds a_o certified |
| A6 | Curvature matrix M bounded |

If assumptions fail, theorems may not hold.

---

## 9.9 Relationship to NK-4G

| NK-4G Interpretation | NEC Theorem |
|----------------------|-------------|
| Spectral gap | Termination (Theorem 5) |
| Descent rate | Per-step descent (Theorem 1) |
| Finite energy | Energy bound (Theorem 2) |
| Center manifold | Fejér monotonicity (Theorem 3) |

NEC provides the algebra. NK-4G provides geometric interpretation.
