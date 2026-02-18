# NEC Compositionality

**Related:** [`7_receipt_witness.md`](7_receipt_witness.md), [`9_soundness_theorems.md`](9_soundness_theorems.md)

---

## 8.1 Why NEC Composes

NEC is compositional because each property localizes to individual operators and batches, enabling safe aggregation.

---

## 8.2 Localization Properties

### Property 1: δ Bounds Localize Change

Each operator o has a bound:

```
|δ_o(x)|_G ≤ a_o
```

This bounds the change from any single operator.

### Lemma 8.1: Sum Bound

For any set of operators B:

```
|Σ_{o∈B} δ_o(x)|_G ≤ Σ_{o∈B} a_o
```

By triangle inequality.

### Implication

Batch displacement is bounded by sum of individual bounds.

---

### Property 2: ε Bounds Control Interaction

The curvature matrix M provides:

```
|ε_{o_i,o_j}| ≤ |M_{ij}|
```

For batch B:

```
|ε_B| ≤ Σ_{i<j} |M_{ij}| · a_i · a_j = ε̂_B
```

### Implication

Interaction between operators is bounded independently of state.

---

### Property 3: Gate Ensures Safe Aggregation

The gate condition:

```
|ε_B| ≤ ε̂_B
```

Ensures that when operators are batched:
- Total residual is bounded
- Witness inequality holds
- Descent structure preserved

---

## 8.3 Reduction to Local Certificates

### Theorem 8.1: Local Certification

Multi-operator execution reduces to local certificates:

```
gate(o_1, x) ∧ gate(o_2, x) ∧ ... ∧ gate(o_n, x)
    ⇒
gate({o_1, ..., o_n}, x)
```

**If** individual operators pass the gate **and** the batch gate passes, then the whole execution is valid.

### Proof Sketch

1. Individual operator bounds → batch displacement bound (Lemma 8.1)
2. Curvature matrix bounds → batch residual bound
3. Gate checks both → execution safe

---

## 8.4 Compositional Proof Structure

### Per-Operator Certificate

```
cert(o) = {
    operator_id: o,
    displacement_bound: a_o,
    invariants: H_o,
    delta_norm: |δ_o|_G
}
```

### Per-Batch Certificate

```
cert(B) = {
    batch_id: B,
    residual_bound: ε̂_B,
    gate_passed: bool,
    witness: w
}
```

### Execution Certificate

```
execution_cert = {
    operator_certs: [cert(o_1), ..., cert(o_n)],
    batch_certs: [cert(B_1), ..., cert(B_m)],
    witness_chain: [w_1, ..., w_m]
}
```

Each piece is independently verifiable.

---

## 8.5 Why This Matters

### Modularity

- Operators can be developed independently
- Batches can be formed dynamically
- Certificates compose additively

### Verification

- Receipt verification is local
- No global state needed
- Parallel verification possible

### Extensibility

- New operator types add new certificates
- New batch strategies still use same structure
- PolicyBundle updates don't require re-verification of old receipts

---

## 8.6 Relationship to NK-3

### NK-3 Lowering

NK-3 lowers programs to operator sets. NEC provides the certificate structure:

| NK-3 Output | NEC Certificate |
|-------------|----------------|
| OpSet | Set of operators |
| DAG | Dependency graph |
| ExecPlan | Batch sequence |
| ModuleReceipt | Certificate chain |

---

## 8.7 Non-Interference

### Lemma 8.2: Non-Interference

If two batches B_1 and B_2 operate on disjoint field sets:

```
gate(x, B_1) ∧ gate(x, B_2) ⇒ gate(x, B_1 ∪ B_2)
```

**Proof**: For disjoint fields, M_{ij} = 0 for o_i ∈ B_1, o_j ∈ B_2, so ε̂_{B_1∪B_2} = ε̂_{B_1} + ε̂_{B_2}.

---

## 8.8 Scalability

### Linear Scaling

Certificate size scales linearly with:
- Number of operators
- Number of batches
- Not with state size

### Verification Complexity

```
O(|operators| + |batches|)
```

Independent of:
- State dimension
- Field count
- History length

---

## 8.9 Summary

| Property | What It Gives |
|----------|---------------|
| δ bounds | Local change control |
| ε bounds | Interaction control |
| Gate | Safe aggregation |
| Witness | Descent proof |
| Compositionality | Modularity + scalability |

These four properties together make NEC the execution algebra that enables deterministic, verifiable batching.
