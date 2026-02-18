# NEC Receipt Witness

**Related:** [`6_split_law.md`](6_split_law.md), [`8_compositionality.md`](8_compositionality.md)

---

## 7.1 Witness Inequality

### Definition 7.1: ProxWitness

The receipt contains a witness inequality that proves descent:

```
V(x_{k+1}) ≤ V(x_k) - (1 / (2·τ·g_k)) · |x_{k+1} - y_k|_G²
```

Where:
- x_k: State before batch
- x_{k+1}: State after batch
- y_k: Proximal point
- τ: Step size parameter
- g_k: Gradient norm factor
- |·|_G²: G-norm squared

---

## 7.2 Proximal Point

### Definition 7.2: Proximal Point

The proximal point y_k is computed from x_k and the batch:

```
y_k = argmin_y { V(y) + (1/(2·τ)) · |x_k - y|_G² }
```

This is the implicit step that gives NEC its stability properties.

### Implementation

For linear/quadratic V:

```
y_k = (I + τ·G)^{-1} · x_k
```

---

## 7.3 Witness Components

### Required Receipt Fields

| Field | Description |
|-------|-------------|
| V_before | V(x_k) |
| V_after | V(x_{k+1}) |
| x_before | emb(x_k) |
| x_after | emb(x_{k+1}) |
| y_k | Proximal point |
| tau | Step size τ |
| g_k | Gradient factor |

### Witness Computation

```
witness = V_after - V_before + (1/(2*tau*g_k)) * norm_G_sq(x_after - y_k)
```

Witness must be ≤ 0 for valid receipt.

---

## 7.4 Verification

### Receipt Verification

The verifier checks:

```
V_after ≤ V_before - (1/(2*tau*g_k)) * |x_after - y|_G²
```

All values are DebtUnit integers.

### Verification Algorithm

```
def verify_witness(receipt):
    lhs = receipt.V_after
    rhs = receipt.V_before - (receipt.tau_factor) * norm_G_sq(receipt.x_after - receipt.y)
    return lhs <= rhs
```

---

## 7.5 Load-Bearing Property

### Why This Matters

The witness inequality is the **load-bearing algebraic guarantee**:

- Proves V never increases
- Bounds total energy expended
- Enables replay verification
- Ensures termination

Without this inequality, receipts would not prove coherence.

---

## 7.6 Relationship to CTD

### CTD Connection

The CTD (Contractual Time Dilation) rule relates to the witness:

```
τ = CTD(V, ε_B)
```

- Larger ε_B → larger τ (slower time)
- Smaller ε_B → smaller τ (faster time)

### Time Accumulation

Over execution:

```
Σ τ_k ≤ ∞  (bounded)
Σ (V_before - V_after) ≤ V_0  (finite energy)
```

---

## 7.7 Receipt Types

### Local Receipt

Emitted after each successful sub-batch:

```
local_receipt = {
    batch: B,
    V_before: V(x),
    V_after: V(x'),
    witness: witness_value,
    operators}
```

### Commit: [...]
 Receipt

Emitted after batch commit:

```
commit_receipt = {
    local_receipts: [...],
    merkle_root: root,
    state_hash: h(x'),
    witness: aggregate_witness
}
```

---

## 7.8 Implementation

### Witness Computation

```
def compute_witness(x_before, x_after, batch, tau, g):
    V_before = V(x_before)
    V_after = V(x_after)
    y = compute_proximal(x_before, tau)
    
    norm_sq = |x_after - y|_G^2
    witness = V_after - V_before + norm_sq / (2 * tau * g)
    
    return witness
```

### Proximal Point

```
def compute_proximal(x, tau):
    # For linear V: y = x (no movement)
    # For quadratic V: y = (I + tau*G)^{-1} * x
    G_inv = diag(1/w_k)  # Inverse of diagonal metric
    return G_inv @ x  # Simplified
```

---

## 7.9 Verification Requirements

### What Verifier Checks

1. Receipt hash chain integrity
2. State transitions are valid
3. Witness inequality holds
4. PolicyBundle matches
5. All operators certified

### What Verifier Does NOT Check

- How proximal point was computed (as long as inequality holds)
- Internal scheduler decisions
- Choice of split (as long as result is valid)

---

## 7.10 Soundness Claim

### Theorem 7.1: Witness Soundness

If a receipt passes verification:
- V decreased (or stayed same)
- Descent bounded by G-norm of movement
- Execution followed NEC rules

The witness is sufficient to prove coherence enforcement.
