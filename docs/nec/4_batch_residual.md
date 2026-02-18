# NEC Batch Residual

**Related:** [`3_delta_norms.md`](3_delta_norms.md), [`5_gate_law.md`](5_gate_law.md)

---

## 4.1 Batch Definition

### Definition 4.1: Batch

A batch B is a set of operators:

```
B = { o_1, o_2, ..., o_m }
```

Batches are the unit of atomic execution in NEC.

### Batch Application

```
x' = patch(x, {δ_o}_{o∈B})
```

The patch function applies all operator displacements to state x.

---

## 4.2 Batch Delta

### Definition 4.2: Batch Displacement

The total displacement from applying batch B:

```
Δx_B = Σ_{o∈B} δ_o(x)
```

Note: This is the sum of individual displacements, not the result of sequential application.

### Norm Bound

From Lemma 3.1:

```
|Δx_B|_G ≤ Σ_{o∈B} a_o
```

---

## 4.3 V Change

### Definition 4.3: Total V Change

```
ΔV_B = V(x') - V(x)
```

Where x' = patch(x, B).

### Definition 4.4: Sum of Individual V Changes

```
ΔV_Σ = Σ_{o∈B} (V(x_o) - V(x))
```

Where x_o is the state after applying operator o individually.

---

## 4.4 Batch Residual

### Definition 4.5: Batch Residual

The batch residual measures non-additivity:

```
ε_B = ΔV_B - ΔV_Σ
```

### Interpretation

| Case | Meaning |
|------|---------|
| ε_B = 0 | V is additive over batch |
| ε_B > 0 | Superadditive (worse than sum) |
| ε_B < 0 | Subadditive (better than sum) |

### Lemma 4.1: Zero Residual

If all operators operate on disjoint fields:

```
ε_B = 0
```

---

## 4.5 Curvature Matrix

### Definition 4.6: Curvature Matrix

The curvature matrix M captures pairwise residuals:

```
M_{ij} = ε_{o_i, o_j}
```

Where for pair (o_i, o_j):

```
ε_{o_i,o_j} = V(x + δ_{o_i} + δ_{o_j}) - V(x + δ_{o_i}) - V(x + δ_{o_j}) + V(x)
```

### Properties

- M is symmetric: M_{ij} = M_{ji}
- Diagonal is zero: M_{ii} = 0

---

## 4.6 Certified Bound

### Definition 4.7: Estimated Batch Residual

The PolicyBundle provides a certified bound:

```
ε̂_B = Σ_{i<j} M_{ij} · a_{o_i} · a_{o_j}
```

### Lemma 4.2: Bound Soundness

For any batch B and state x:

```
|ε_B| ≤ ε̂_B
```

The bound uses operator bounds a_o and curvature matrix M.

---

## 4.7 Implementation

### Computation

```
def compute_batch_residual(x, B):
    # Total V change
    x_prime = patch(x, B)
    delta_V_B = V(x_prime) - V(x)
    
    # Sum of individual changes
    delta_V_sigma = 0
    for o in B:
        x_o = apply(o, x)
        delta_V_sigma += V(x_o) - V(x)
    
    return delta_V_B - delta_V_sigma
```

### Bound Check

```
def check_batch_bound(B):
    epsilon_hat = sum(M[i][j] * a[i] * a[j] for i < j)
    return epsilon_hat <= bound_from_policy()
```

---

## 4.8 Relationship to NK-4G

| NK-4G Concept | NEC Batch Residual |
|---------------|---------------------|
| ε_B | Same |
| M matrix | Same |
| Non-additivity | Same |
| G-norm | Same |

NEC defines the computation. NK-4G provides geometric interpretation.
