# NEC Contract Structure

**Related:** [`1_state_space.md`](1_state_space.md), [`3_delta_norms.md`](3_delta_norms.md)

---

## 2.1 Contract Definition

### Definition 2.1: Contract

A contract C is a tuple:

```
C = (H, S, Θ)
```

Where:
- H: Hard invariants
- S: Soft constraints  
- Θ: Parameter map

### Components

| Component | Type | Enforced By |
|-----------|------|-------------|
| H | Set of predicates | Rejection (not penalized) |
| S | Set of soft constraints | V(x) functional |
| Θ | Parameter mapping | PolicyBundle |

---

## 2.2 Hard Invariants H

### Definition 2.2: Hard Invariants

```
H = { h_i : X → Bool }
```

Hard invariants are boolean predicates that must hold for valid states.

### Enforcement

If any h_i(x) = false:
- State x is invalid
- Transition is rejected
- No V computation performed

### Examples

```
h_1: debt ≥ 0
h_2: budget ≥ 0
h_3: state_hash ∈ valid_set
```

---

## 2.3 Soft Constraints S

### Definition 2.3: Soft Constraints

```
S = { s_j : X → ℝ_{≥0} }
```

Soft constraints map to non-negative real values representing violation magnitude.

### V Encoding

The violation functional V encodes all soft constraints:

```
V(x) = Σ_j w_j · s_j(x)
```

Where w_j are weights from PolicyBundle.

---

## 2.4 Parameter Map Θ

### Definition 2.4: Parameter Map

```
Θ : ParamID → Value
```

Maps parameter identifiers to values from PolicyBundle.

### Examples

```
Θ("DEBT_SCALE") = 2^16
Θ("SIGMA_SPEC") = "sigma_linear"
Θ("WEIGHT_SPEC") = weight_vector
```

---

## 2.5 Contract Lifecycle

### Creation

```
C = create_contract(H, S, Θ)
  → policy_digest = h(C)
  → PolicyBundle bound
```

### Execution

For each state x:
1. Check H: if any fail → reject
2. Compute V(x) from S
3. Record in receipt

### Verification

Receipt contains:
- H status (pass/fail)
- V(x) value
- Parameter hash

---

## 2.6 Relationship to NK-1

| NK-1 Concept | NEC Contract |
|---------------|---------------|
| InvariantSet | H |
| ViolationFunctional | S encoded in V |
| PolicyBundle | Θ |
| Measured gate | V check against bound |

NEC contract structure maps directly to NK-1 implementation.
