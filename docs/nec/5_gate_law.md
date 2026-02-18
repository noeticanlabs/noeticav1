# NEC Gate Law

**Related:** [`4_batch_residual.md`](4_batch_residual.md), [`6_split_law.md`](6_split_law.md)

---

## 5.1 Gate Condition

### Definition 5.1: Gate

The gate is a safety condition that must pass before batch execution:

```
gate(x, B) = (|ε_B| ≤ ε̂_B)
```

Where:
- ε_B is the actual batch residual (computed)
- ε̂_B is the certified bound (from PolicyBundle)

### Gate Decision

| Condition | Result |
|-----------|--------|
| |ε_B| ≤ ε̂_B | PASS → Execute batch |
| |ε_B| > ε̂_B | FAIL → Split or reject |

---

## 5.2 Certified Bound

### Definition 5.2: Estimated Batch Residual

From PolicyBundle:

```
ε̂_B = Σ_{i<j} M_{ij} · a_{o_i} · a_{o_j}
```

Where:
- M_{ij} is the curvature matrix entry
- a_{o_i} is the operator bound for o_i

### Bound Components

| Component | Source |
|-----------|--------|
| M_{ij} | PolicyBundle.curvature_matrix |
| a_{o_i} | Operator certificate |
| ε̂_B | Computed from above |

---

## 5.3 Gate Soundness

### Lemma 5.1: Bound Implication

If gate passes:

```
|ε_B| ≤ ε̂_B  ⇒  |ε_B| ≤ Σ_{i<j} |M_{ij}| · a_i · a_j
```

This bounds the actual residual by the certified bound.

### Theorem 5.1: Gate Soundness

The gate condition ensures:

```
If gate(x, B) passes, then the multi-operator execution preserves bounded descent structure.
```

See [`9_soundness_theorems.md`](9_soundness_theorems.md) for proof.

---

## 5.4 Integer Comparisons

### Requirement: Exact Comparison

All gate comparisons use integer arithmetic:

```
|ε_B|_DU ≤ ε̂_B_DU
```

Where both are DebtUnit integers.

### No Floating Point

- No floating comparisons at gate
- All bounds are integer DebtUnit
- Rounding: half-even for any conversion

---

## 5.5 Gate Failure

### Failure Modes

| Failure Type | Handling |
|--------------|----------|
| ε_B > ε̂_B | Split batch (see §6) |
| Singleton fails | Terminal halt |
| Hard invariant violation | Reject without gate |

### Error Reporting

On gate failure:

```
error = {
    code: GATE_FAILED,
    batch: B,
    epsilon_actual: ε_B,
    epsilon_bound: ε̂_B,
    operator: failing_operator
}
```

---

## 5.6 Relationship to NK-1

| NK-1 Concept | NEC Gate Law |
|--------------|--------------|
| Measured gate | gate() function |
| ε_measured | ε_B (actual) |
| ε_hat | ε̂_B (bound) |
| Gate decision | PASS/FAIL |

The measured gate in NK-1 implements the NEC gate law.

---

## 5.7 Implementation

### Gate Check

```
def gate(x, B):
    # Compute actual residual
    epsilon_B = compute_batch_residual(x, B)
    
    # Get certified bound
    epsilon_hat = compute_epsilon_hat(B)
    
    # Compare
    return abs(epsilon_B) <= epsilon_hat
```

### Batched Gate

For performance, pre-compute ε̂_B for all possible batches:

```
precomputed[batch_id] = ε̂_B
```

---

## 5.8 Policy Binding

### Required Policies

| Policy | Purpose |
|--------|---------|
| curvature_matrix | M_{ij} values |
| operator_bounds | a_o for each operator |
| bound_function | How to compute ε̂_B |

All bound into PolicyBundle hash.

### Changing Bounds

To change bounds:
1. Create new PolicyBundle
2. New policy_digest
3. Verify all operators recertified
