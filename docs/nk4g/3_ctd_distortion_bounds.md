# NK-4G CTD Distortion Bounds

**Related:** [`2_curvature_definition.md`](2_curvature_definition.md), [`4_spectral_analysis.md`](4_spectral_analysis.md)

---

## 3.1 CTD Rule

### Definition 3.1: Internal Time Increment

The CTD (Contractual Time Dilation) rule computes internal time increment:

```
δ_b = Φ(V(x), ε_B)
```

Where:
- `V(x)` is the current violation functional value
- `ε_B` is the batch residual
- `Φ` is the CTD function from PolicyBundle

### Policy Binding

The function hash `h(Φ)` is bound in PolicyBundle:

```
PolicyBundle.ctd_function_hash = h(Φ)
```

Changing Φ requires new PolicyBundle (different policy_digest).

---

## 3.2 Lipschitz Bound

### Assumption 3.1: Lipschitz CTD

Assume Φ is Lipschitz in ε_B on the reachable region ℛ:

```
|Φ(V, ε₁) - Φ(V, ε₂)| ≤ L_max · |ε₁ - ε₂|
```

For all V in domain, ε₁, ε₂ in range.

### Lemma 3.1: Distortion Bound

Under Assumption 3.1:

```
|δ_b| ≤ L_max · |ε_B|
```

**Proof:**

```
|δ_b| = |Φ(V, ε_B) - Φ(V, 0)|  (assuming Φ(V, 0) = 0)
    ≤ L_max · |ε_B - 0|
    = L_max · |ε_B|
```

This is the fundamental distortion bound used in CTD stability analysis.

---

## 3.3 Accumulated Distortion

### Definition 3.2: Accumulated Distortion

Let a execution consist of batches `B₁, B₂, ..., B_T`. Define:

```
Δ_τ^tot = Σ_{t=1}^{T} δ_b(t)
```

The total internal time increment over τ steps.

### Lemma 3.2: Telescoping Bound

Under Lemma 3.1:

```
|Δ_τ^tot| ≤ L_max · Σ_{t=1}^{T} |ε_{B_t}|
```

### Definition 3.3: Estimated Batch Residual

Let `ε̂_B` be the estimated (predicted) batch residual from PolicyBundle:

```
ε̂_B = ε_B^estimate
```

The PolicyBundle provides bounds:

```
|ε_B| ≤ ε̂_B  (with probability 1, deterministically)
```

### Theorem 3.1: CTD-BS Bound

```
|Δ_τ^tot| ≤ L_max · Σ_{t=1}^{T} ε̂_{B_t}
```

This matches the CTD-Bounded-Sum theorem from NK-1/NK-2.

---

## 3.4 Implications

### Bounded Internal Time

If Σ ε̂_B_t is bounded over all executions:

```
Σ_{t=1}^{∞} ε̂_{B_t} < ∞  ⇒  Δ_τ^tot converges
```

This provides termination guarantees.

### Distortion as Error Signal

| Condition | Interpretation |
|-----------|----------------|
| L_max small | CTD is "flat" - time tracks real time |
| L_max large | CTD amplifies residuals - faster internal time |
| ε_B small | Batch is "linear" - low curvature |
| ε_B large | Batch is "curved" - high non-additivity |

---

## 3.5 Relationship to NK-2

NK-4G interpretation of NK-2:

| NK-2 Concept | NK-4G Interpretation |
|--------------|---------------------|
| CTD rule | Lipschitz function Φ |
| Batch execution | ε_B computation |
| Termination | Bounded Σ ε̂_B |
| Scheduler | Minimizes ε̂_B (greedy.curv.v1) |

---

## 3.6 Constants

| Constant | Symbol | Source |
|----------|--------|--------|
| Lipschitz bound | L_max | PolicyBundle |
| Estimated residual | ε̂_B | PolicyBundle |
| Residual bound | C_ε | NEC closure |
