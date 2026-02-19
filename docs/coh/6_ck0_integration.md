# Coh_CK0 Integration

**Status:** Canonical  
**Layer:** L1 → Subcategory

---

## Overview

CK-0 is a **full subcategory** of Coh, denoted:

```
Coh_CK0 ⊆ Coh
```

This means:
- Objects of Coh_CK0 are Coh objects satisfying CK-0 canonical form
- Morphisms of Coh_CK0 are Coh morphisms between CK-0 objects

---

## Coh_CK0 Object Definition

A Coh object is CK-0-compatible if:

### 1. Potential has weighted residual form

```
V(x) = r̃(x)ᵀ W r̃(x)
```

where:
- r̃(x) is the residual vector (soft residual)
- W is a fixed SPD weight matrix

Or equivalently, normalized sum-of-squares.

### 2. Receipts have CK-0 schema

Each receipt ρ contains:
- policy_id: Policy identifier
- budget: Declared service budget
- debt: Current debt
- residual: r̃(x) values
- hash: Cryptographic digest
- timestamp: Service time

### 3. Validator enforces CK-0 descent theorem

The validate function enforces:

```
V(y) ≤ V(x) - δ(ρ) + Δ(ρ)
```

where:
- δ(ρ) is the service reduction from the receipt
- Δ(ρ) is the budget allowance

---

## CK-0 Object Predicate

```python
def is_ck0_compatible(obj: CohObject) -> bool:
    """Check if Coh object satisfies CK-0 canonical form"""
    
    # 1. V has weighted residual form (implementation-specific check)
    # This may require examining the structure of the potential function
    
    # 2. RV receipts have required CK-0 fields
    # Check that validate function enforces CK-0 descent theorem
    
    # 3. Gate law satisfied (NK-1 batch aggregation)
    # This is an additional structural constraint
    
    return True  # Placeholder - actual implementation depends on model
```

---

## Coh_CK0 Morphisms

A morphism in Coh_CK0 is a Coh morphism:

```
f: S₁ → S₂
```

where S₁ and S₂ are both CK-0-compatible.

The morphism must additionally preserve the CK-0 structure:
- State map preserves residual structure
- Receipt map preserves CK-0 fields

---

## Integration with Existing CK-0

### Current CK-0 becomes Coh_CK0

The existing CK-0 specification is reinterpreted as:

| CK-0 Concept | Coh_CK0 Representation |
|--------------|----------------------|
| Violation functional V | Potential functional V |
| Admissible set C | C = V⁻¹(0) |
| Receipt theorem | RV with CK-0 descent inequality |
| Repair order | Reachability preorder from T |
| Budget/debt law | Additional receipt field constraints |

### Backward Compatibility

Existing CK-0 code continues to work:
- CK-0 objects are valid Coh objects
- CK-0 transitions are valid Coh morphisms
- CK-0 proofs are valid in the categorical framework

---

## Functorial Relationship

### Inclusion Functor

```
I: Coh_CK0 → Coh
```

The inclusion is a faithful functor:
- On objects: identity (Coh_CK0 objects are Coh objects)
- On morphisms: identity (CK-0 morphisms are Coh morphisms)

### Violation Functor (restricted)

```
Vio|_CK0: Coh_CK0 → Set^ℝ≥0
```

Maps CK-0 objects to their violation functionals.

---

## Implementation Notes

```python
class CohCK0Object(CohObject):
    """Coh object with CK-0 canonical form"""
    
    def __init__(self, residual_fn, weight_matrix, receipt_schema, validate_fn):
        super().__init__(
            is_state=...,
            is_receipt=...,
            potential=lambda x: residual_fn(x) @ weight_matrix @ residual_fn(x),
            budget_map=...,
            validate=validate_fn
        )
        self.weight_matrix = weight_matrix
        self.receipt_schema = receipt_schema
    
    @staticmethod
    def is_ck0(obj: CohObject) -> bool:
        """Check CK-0 compatibility"""
        # Verify V has weighted residual form
        # Verify receipts have required fields
        # Verify gate law
        pass

class CohCK0Category(CohCategory):
    """Full subcategory of Coh on CK-0 objects"""
    
    def compose(self, f, g):
        result = super().compose(f, g)
        # Verify result is still CK-0 compatible
        return result
```

---

## Conformance Points

| Property | Test |
|----------|------|
| Object compatibility | is_ck0(S) returns True |
| Morphism compatibility | f: S₁→S₂ with S₁,S₂ CK-0 |
| Inclusion functor | I: Coh_CK0 → Coh is faithful |
| Backward compatibility | Existing CK-0 = valid Coh_CK0 |

---

## Notes

- Coh_CK0 is a full subcategory: morphisms have same structure as in Coh
- The integration is surgical: no duplication, maximal composability
- Future extensions (KL divergence, manifolds, lattices) can be added as other full subcategories
