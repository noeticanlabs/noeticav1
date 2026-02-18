# NEC State Space

**Related:** [`0_overview.md`](0_overview.md), [`2_contract_structure.md`](2_contract_structure.md)

---

## 1.1 State Space Definition

Let X denote the canonical NK-1 state space.

### Definition 1.1: State Space

```
X = { x : FieldID → Value }
```

Where:
- FieldID is a fixed-length identifier (32 hex chars)
- Value is a typed value (integer, blob, reference)

### Definition 1.2: Numeric Embedding

For computation, states are embedded to numeric vectors:

```
emb(x) = [f_1, f_2, ..., f_n] ∈ ℤ^n
```

Where each f_i is a quantized integer value.

---

## 1.2 Coherence Functional V

### Definition 1.3: Violation Functional

```
V : X → ℝ_{≥0}
```

V maps states to non-negative real numbers representing contract violation.

### Definition 1.4: DebtUnit Representation

For implementation, V is represented as integer DebtUnit:

```
V_DU : X → ℤ_{≥0}
```

```
V(x) = V_DU(x) / DEBT_SCALE
```

Where DEBT_SCALE is a fixed power of 2 from PolicyBundle.

### Requirement: No Floating Semantics

V computation must use:
- Exact integer arithmetic in DebtUnit
- Half-even rounding for conversion
- No floating point at any stage

---

## 1.3 Reachability

### Definition 1.5: Reachable Region

Let ℛ ⊆ X denote the reachable region:

```
ℛ = { x ∈ X : x is reachable via valid NEC transitions }
```

NEC theorems hold for all x ∈ ℛ.

---

## 1.4 Relationship to CK-0

| CK-0 Concept | NEC Representation |
|--------------|---------------------|
| State space X | Same |
| V(x) | Same (DebtUnit integer) |
| Typed fields | Numeric embedding |
| Field blocks | Vector structure |

NEC uses CK-0 definitions but adds operational semantics.
