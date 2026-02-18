# NEC Receipt Witness

**Related:** [`6_split_law.md`](6_split_law.md), [`8_compositionality.md`](8_compositionality.md)

---

## 7.1 Witness Inequality

### Definition 7.1: ProxWitness

The receipt contains a witness inequality that proves proximal correction in the split model:

```
V(x_{k+1}) ≤ V(z_k) - (1 / (2·λ_k)) · |x_{k+1} - z_k|_G²
```

**Canonical Split Model:**
- **Drift**: z_k = U_τ x_k (proposal from model, may increase V)
- **Correction**: x_{k+1} = prox_{λ_k V}(z_k) = argmin_x { V(x) + (1/2λ_k)|x-z_k|_G² }
- **Witness**: V(x_{k+1}) ≤ V(z_k) - (1/2λ_k)||x_{k+1}-z_k||_G²

Where:
- x_k: State before batch
- z_k: **Drift point** (proposal from model, replaces old y_k)
- x_{k+1}: State after correction
- λ_k: Prox parameter (renamed from τ for consistency)
- |·|_G²: G-norm squared

**Note:** V(z_k) may be > V(x_k) due to drift. The witness proves correction reduces V from the drift point, not from the original state.

---

## 7.2 Drift and Correction Points

### Definition 7.2: Drift Point z_k

The drift point is the state after applying the model's proposal/evolution:

```
z_k = U_τ x_k
```

Where U_τ represents the model dynamics (e.g., unitary drift, resonance operator).

**Important:** z_k may have V(z_k) > V(x_k) - drift can increase violation.

### Definition 7.2b: Correction (Proximal)

The correction point is the result of proximal minimization:

```
x_{k+1} = prox_{λ_k V}(z_k) = argmin_x { V(x) + (1/(2·λ_k)) · |x - z_k|_G² }
```

This is the implicit step that gives NEC its stability properties.

### Implementation

For linear/quadratic V with scalar λ:

```
x_{k+1} = (I + λ_k·G)^{-1} · z_k
```

---

## 7.3 Witness Components

### Required Receipt Fields

| Field | Description |
|-------|-------------|
| V_before | V(x_k) |
| V_after | V(x_{k+1}) |
| V_drift | V(z_k) - **NEW: drift point violation** |
| x_before | emb(x_k) |
| x_after | emb(x_{k+1}) |
| z_k | **Drift point** (replaces old y_k) |
| lambda_k | Prox parameter λ_k (renamed from tau) |

### Witness Computation

```
witness = V_after - V_drift + (1/(2*lambda_k)) * norm_G_sq(x_after - z_k)
```

Witness must be ≤ 0 for valid receipt.

**Note:** V_drift = V(z_k) may be > V_before. The witness proves correction from drift, not from original state.

---

## 7.4 Verification

### Receipt Verification

The verifier checks:

```
V_after ≤ V_drift - (1/(2*lambda_k)) * |x_after - z_k|_G²
```

All values are DebtUnit integers.

### Verification Algorithm

```
def verify_witness(receipt):
    lhs = receipt.V_after
    rhs = receipt.V_drift - (1/(2*receipt.lambda_k)) * norm_G_sq(receipt.x_after - receipt.z_k)
    return lhs <= rhs
```

**Note:** This verifies correction from drift point z_k, not from original state x_k.

---

## 7.5 Load-Bearing Property

### Why This Matters

The witness inequality is the **load-bearing algebraic guarantee**:

- Proves V decreases from drift point: V(x_{k+1}) ≤ V(z_k)
- **Note:** V(z_k) may be > V(x_k) due to drift. The witness proves correction, not that V never increases.
- Bounds total energy expended in correction step
- Enables replay verification
- Ensures termination

Without this inequality, receipts would not prove coherence.

**Split Model Property:**
```
V(x_{k+1}) ≤ V(z_k) - (1/2λ_k)||x_{k+1}-z_k||² ≤ V(z_k)
```
The inequality proves correction reduces V from the drift point, not from the original state.

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
