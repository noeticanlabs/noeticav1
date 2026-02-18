# NEC Delta Norms

**Related:** [`2_contract_structure.md`](2_contract_structure.md), [`4_batch_residual.md`](4_batch_residual.md)

---

## 3.1 Operator Displacement

### Definition 3.1: Operator

An operator o is a state transformation:

```
o : X → X
```

Operators are the atomic execution units in NEC.

### Definition 3.2: Displacement

For operator o applied to state x:

```
δ_o(x) = emb(o(x)) - emb(x) ∈ ℤ^n
```

The displacement is the difference in numeric embeddings.

---

## 3.2 G-Norm

### Definition 3.3: Weight Vector

From PolicyBundle, weights w_k > 0:

```
w = [w_1, w_2, ..., w_n] ∈ ℕ^n
```

Weights are static and policy-locked.

### Definition 3.4: G-Norm

```
|δ_o(x)|_G² = Σ_k w_k · (δ_o(x)_k)²
```

The weighted squared norm under diagonal metric G = diag(w).

### Integer Implementation

All computations use DebtUnit integers:

```
|δ_o(x)|_G² ∈ ℤ_{≥0}
```

---

## 3.3 Displacement Bounds

### Definition 3.5: Operator Bound

Each operator o has a certified bound a_o:

```
|δ_o(x)|_G ≤ a_o   for all x ∈ ℛ
```

The bound a_o is:
- Encoded in DebtUnit
- Policy-locked in PolicyBundle
- Verified at compile time

### Bound Certificate

```
cert(o) = {
    operator_id: o,
    bound: a_o,
    proof: <verification>
}
```

---

## 3.4 Bound Properties

### Lemma 3.1: Bound Consistency

If operators o_1, ..., o_m all satisfy:

```
|δ_{o_i}(x)|_G ≤ a_{o_i}
```

Then for any subset B ⊆ {o_i}:

```
|Σ_{o∈B} δ_o(x)|_G ≤ Σ_{o∈B} a_o  (triangle inequality)
```

### Lemma 3.2: Bound Tightness

Bounds are tight in worst case:

```
max_{x∈ℛ} |δ_o(x)|_G = a_o
```

---

## 3.5 Relationship to CK-0

| CK-0 Concept | NEC Delta Norm |
|--------------|----------------|
| Transition δ | δ_o(x) |
| G-metric | Same weights w |
| Bound a_o | Same |
| Field ordering | Canonical lex order |

NEC delta norms are the operational version of CK-0 transition bounds.

---

## 3.6 Implementation

### Computation

```
def compute_delta_norm(x, o):
    delta = emb(o(x)) - emb(x)
    return sum(w_k * delta_k^2 for k in fields)
```

All in DebtUnit integers.

### Verification

```
def verify_bound(o, x):
    norm_sq = compute_delta_norm(x, o)
    return norm_sq <= a_o^2
```
