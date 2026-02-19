# Zero-Cost Coherence

**Version:** 1.0  
**Status:** Draft  
**Related:** [`9_security_model.md`](9_security_model.md), [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)

---

## 10.1 Goal

The goal of **zero-cost coherence** is to ensure that the hot path (the inner loop of solve/repair operations) contains **no refinement checks** while still maintaining the coherence guarantees.

### Principle

> Coherence enforcement must not be in the critical path. It happens at the boundary, not in the loop.

---

## 10.2 Hot Loop Requirements

### What Goes in the Hot Loop

| Operation | In Hot Loop | Rationale |
|-----------|-------------|-----------|
| Gradient computation | ✓ | Core computation |
| State updates | ✓ | Must be fast |
| Curvature updates | ✓ | Must be fast |
| Budget subtraction | ✓ | Atomic arithmetic |
| Phase flag check | ✓ | Single comparison |

### What Does NOT Go in Hot Loop

| Operation | In Hot Loop | Rationale |
|-----------|-------------|-----------|
| Refinement predicate check | ✗ | Compile-time proven |
| Full V(x) computation | ✗ | Only at boundary |
| Receipt emission | ✗ | Only at boundary |
| Authority injection | ✗ | Only at boundary |
| Mint/Burn | ✗ | Only at boundary |

---

## 10.3 Demonstration Requirements

### Requirement 1: No Budget Branch in Loop

The hot loop must NOT contain:

```
if (budget <= 0) { branch }
```

Instead, the budget is guaranteed positive by construction:
- Compiler ensures sufficient budget at loop entry
- Runtime only executes loop when budget > 0

### Requirement 2: No Refinement Check in Loop

The hot loop must NOT contain:

```
if (V(x') > V(x) + Θ) { fail }
```

Instead:
- Refinement is proven at compile time
- Only arithmetic operations in loop

### Requirement 3: Only Arithmetic in Loop

Hot loop operations limited to:

- Integer addition/subtraction
- Integer multiplication (by constants)
- Array indexing
- Phase flag check

### Requirement 4: Phase Check is O(1)

The phase check is a single comparison:

```
if (phase == Loom) { /* solve */ }
```

Not a complex predicate check.

---

## 10.4 Code Structure

### Hot Loop (Solve)

```noetica
// Entry: budget > 0, phase = Loom guaranteed by type system
// This is the hot path - no checks inside
let solve_loop = {
    // Gradient computation (arithmetic only)
    grad = compute_gradient(state, params);
    
    // State update (arithmetic only)
    state' = state - lr * grad;
    
    // Budget update (arithmetic only)
    budget' = budget - cost;
    
    // Loop condition (phase check is O(1))
    if (budget' > 0) { solve_loop } else { exit }
};
```

### Boundary (Refinement)

```noetica
// This runs ONCE before the hot loop
let pre_check = {
    // Refinement proof happens at compile time
    // Runtime just verifies entry conditions
    if (budget >= min_budget) {
        solve_loop
    } else {
        fail  // Compile-time error if this branch reachable
    }
};
```

---

## 10.5 Compile-Time Proof Obligations

### Before Hot Loop

The compiler must prove:

1. **Budget sufficiency**: `budget > 0` at entry
2. **Phase correctness**: `phase = Loom` at entry
3. **Refinement guarantee**: `V(x') ≤ V(x) + Θ` for any loop iteration

### Refinement in Hot Loop

The compiler proves:

```
∀ iteration i.
    V(state_i) ≤ V(state_0) + i * cost_per_iteration
```

This is guaranteed because:
- Gradient descent reduces V by at least δ per iteration
- Cost per iteration = c × δ (where c is constant)
- Therefore V always stays within bound

---

## 10.6 Performance Characteristics

### Hot Loop Cost

| Operation | Cycles (estimated) |
|-----------|-------------------|
| Gradient compute | 100-1000 |
| State update | 50-100 |
| Budget subtract | 1 |
| Phase check | 1 |
| Loop overhead | 5 |

### Boundary Cost

| Operation | Cycles (estimated) |
|-----------|-------------------|
| Refinement check | 10000-100000 |
| V(x) compute | 50000-500000 |
| Receipt emit | 10000-50000 |

**Conclusion**: Boundary cost is 100-1000x more expensive than hot loop. This justifies zero-cost coherence.

---

## 10.7 Verification

### Static Verification

1. **Type checking**: Ensures linear resources are consumed
2. **Phase checking**: Ensures solve only in Loom
3. **Refinement proof**: Proves V bound using CK-0 lemmas

### Dynamic Verification

1. **Budget guard**: Prevents negative budget
2. **Phase guard**: Prevents wrong-phase execution
3. **Receipt**: Proves boundary conditions were met

### STF Verification

The NK-4G verifier checks:
- Receipt chain integrity
- Budget conservation
- Phase transitions
- Refinement bound

---

## 10.8 References

- Security model: [`9_security_model.md`](9_security_model.md)
- Integration: [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)
- Kernel spec: [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)
- Refinement: [`4_refinement_profile_v1.md`](4_refinement_profile_v1.md)
