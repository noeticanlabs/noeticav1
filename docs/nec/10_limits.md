# NEC Limits

**Related:** [`9_soundness_theorems.md`](9_soundness_theorems.md), [`0_overview.md`](0_overview.md)

---

## 10.1 What NEC Guarantees

### Guarantees Provided

NEC guarantees:

| Guarantee | Description |
|-----------|-------------|
| Deterministic execution | Same inputs → same outputs |
| Bounded interaction | ε_B ≤ ε̂_B via gate |
| Verifiable descent | Witness inequality |
| Finite energy | Σ movement ≤ V(x₀) |
| Fejér monotonicity | Sequence bounded |
| Receipt verifiability | Chain checkable |

### Required Conditions

Guarantees hold when:

1. All operators pass gate
2. V is bounded below
3. τ_k, g_k > 0 and bounded
4. Operator bounds certified
5. Curvature matrix M bounded

---

## 10.2 What NEC Does NOT Guarantee

### Convergence

| Non-Guarantee | Reason |
|---------------|--------|
| Convergence to minimum | Only descent, not optimization |
| Rate of convergence | Depends on V landscape |
| Optimal scheduling | Scheduler is heuristic |
| Global minimum | Local descent only |

### Without Convexity

| Non-Guarantee | Reason |
|---------------|--------|
| Global convergence | Requires convexity |
| Unique minimum | May have multiple local minima |
| Exponential rate | Only with strong convexity |
| Stationary point | May get stuck in local minimum |

### Without Spectral Gap

| Non-Guarantee | Reason |
|---------------|--------|
| Fast convergence | Requires λ_min > 0 |
| Linear rate | Requires strong convexity |
| Guaranteed progress | May experience metastability |

---

## 10.3 Explicit Non-Claims

NEC does NOT claim:

### Correctness

- Contract satisfaction (NK-1 guarantees this)
- Resource bounds (NK-2 guarantees this)
- Safety properties (separate verification)

### Performance

- Scheduling optimality
- Throughput
- Latency
- Memory usage

### Termination

- Convergence to V = 0
- Finite time termination (only bounded energy)
- Progress without convexity

---

## 10.4 Assumptions Required

### For Termination

```
Assumption T1: V bounded below (V* ≥ 0)
Assumption T2: All batches pass gate
Assumption T3: τ_k > 0 for all k
```

### For Convergence

```
Assumption C1: V is convex
Assumption C2: Strong convexity (λ_min > 0)
Assumption C3: Step sizes satisfy conditions
```

### For Rate Guarantees

```
Assumption R1: Lipschitz gradient
Assumption R2: Bounded Hessian
Assumption R3: Spectral gap ≥ λ_min > 0
```

---

## 10.5 Failure Modes

### Known Failure Modes

| Mode | Condition | Consequence |
|------|-----------|-------------|
| Gate failure | ε_B > ε̂_B | Split or halt |
| Singleton failure | gate({o}) fails | Terminal halt |
| Hard invariant fail | h_i(x) = false | Reject |
| Resource cap | resource > limit | Terminal halt |
| Zero spectral gap | λ_min = 0 | Metastability |

### Not Failures

These are expected behavior, not bugs:

| Case | Not a Bug Because |
|------|------------------|
| No convergence to 0 | Only guarantees descent |
| Slow convergence | No convexity guarantee |
| Metastability | Expected with zero-gap |
| Halting with V > 0 | Valid terminal state |

---

## 10.6 Limits Summary

| Aspect | Limit |
|--------|-------|
| Convergence | Only descent, not optimization |
| Rate | Not guaranteed |
| Scheduling | Heuristic, not optimal |
| Global properties | Local only |
| Without convexity | Limited guarantees |

---

## 10.7 Relationship to NK-4G

### What NK-4G Adds

NK-4G geometric interpretation explains:
- Why convergence is slow (spectral gap small)
- Why metastability occurs (λ_min = 0)
- How to improve (regularization)

### What NK-4G Doesn't Fix

NK-4G is interpretive only:
- Cannot fix non-convergence
- Cannot add convexity
- Cannot guarantee rates

---

## 10.8 Design Philosophy

NEC is designed to:

1. **Guarantee determinism** - Always
2. **Bound interaction** - Via gate
3. **Enable verification** - Via receipts
4. **Not over-promise** - Explicit limits

This is why NEC has explicit limits - it guarantees what it can prove, and clearly states what it cannot guarantee.

---

## 10.9 Summary

NEC provides:
- Algebraic execution law
- Bounded interaction
- Verifiable descent
- Deterministic batching

NEC does NOT provide:
- Convergence guarantees
- Optimality
- Global properties
- Performance guarantees

Know the limits. Use NK-4G for interpretation when needed.
