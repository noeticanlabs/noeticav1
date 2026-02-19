# Morphism Semantics: Global vs Instance

This document clarifies the distinction between global morphism properties and instance morphism certification in the Coh–PoC–LoC framework.

---

## 1. Global Morphism Property

### 1.1 Definition

A **global morphism** `f: A → B` satisfies:

```
V_B(f(x)) ≤ V_A(x)  ∀x ∈ X_A
```

This is a **universal quantification** over all states in the domain.

### 1.2 Meaning

This property means:
- The morphism is inherently non-inflating
- For any starting state, the potential never increases
- This is a **design-time property** of the morphism structure

### 1.3 When It Applies

Global morphism properties are relevant when:
- Defining morphism classes (e.g., "all coherent updates")
- Proving categorical properties
- Building functorial structures

---

## 2. Instance Morphism Certification

### 2.1 Definition

An **instance morphism** is a specific executed transition:

```
f: x → x'  with receipt π
```

This is a **single, concrete transition** verified by the runtime.

### 2.2 Verification

The verifier (NK-4G) checks:
1. `x` is a valid state in domain
2. `x'` is a valid state in codomain  
3. `π` is a valid receipt
4. `RV(x, x', π)` holds
5. Budget conservation: `b_before ≥ b_after + cost(f)`

### 2.3 When It Applies

Instance certification is what happens at **runtime**:
- Each executed transition produces a receipt
- The receipt is verified by NK-4G
- Budget is decremented accordingly

---

## 3. The Operational Distinction

### 3.1 Design Time vs Runtime

| Aspect | Global Morphism | Instance Certification |
|--------|-----------------|----------------------|
| **When** | Design/proof time | Runtime |
| **What** | Property over all x | Single (x, x', π) |
| **Who** | Developer/verifier | NK-4G executor |
| **Quantification** | ∀x | ∃x (specific) |

### 3.2 Why Both Matter

- **Global properties** let us prove categorical structure
- **Instance certification** lets us execute transitions safely

The global property guarantees that *if* we execute a valid instance, it will be non-inflating.

---

## 4. Coh_rcpt: Receipt Discipline

### 4.1 Definition

`Coh_rcpt` is the receipt-discipline variant where:
- Receipts are deterministic
- No retry allowed
- Subadditivity is structurally enforceable

### 4.2 Instance-Only Verification

In `Coh_rcpt`, we verify:
- This specific transition
- This specific receipt
- This specific budget expenditure

We **don't** verify the global property at runtime - we rely on:
1. The morphism being constructed correctly
2. The verification ensuring the instance is valid

### 4.3 Soundness

If all instances are verified and budgets conserved, the global property holds as a corollary (by construction of the morphism).

---

## 5. Mathematical Relationship

### 5.1 Instance from Global

If `f` is a global non-inflating morphism, then for any instance:
```
V_B(x') ≤ V_A(x)
```
automatically holds (by the global property).

### 5.2 Global from Instances

The converse doesn't hold - you can't prove a global property from finitely many instances (for infinite state spaces).

### 5.3 Practical Approach

In practice:
1. **Define** morphisms that satisfy global property (by construction)
2. **Execute** instances that are individually verified
3. **Trust** that all instances inherit the property

---

## 6. Code Representation

### 6.1 CohMorphism

```python
from coh.types import CohMorphism

# Global morphism structure
f = CohMorphism(
    state_map=lambda x: update(x),
    receipt_map=lambda rho: transport(rho),
    domain=A,
    codomain=B
)
```

### 6.2 Instance Verification

```python
from ck0.cost import verification_cost
from coh.grothendieck import morphism_exists, Budget

# Instance verification
instance = Instance(
    morphism=f,
    pre_state=x,
    post_state=x_prime,
    receipt=pi,
    budget_before=Budget(100),
    budget_after=Budget(95)
)

# Check budget conservation
if morphism_exists(f, instance.budget_before, instance.budget_after, config):
    # Instance is valid!
    pass
```

---

## 7. References

- `src/coh/types.py` - CohMorphism definition
- `src/coh/morphisms.py` - M1, M2 verification
- `src/nk4g/verifier.py` - Instance certification
- `src/coh/grothendieck.py` - Budget conservation
