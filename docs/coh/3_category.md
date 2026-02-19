# Coh Category Structure

**Canonical ID:** `coh.category.v1`  
**Status:** Canonical  
**Section:** §6

---

## Category Axioms

**Coh** forms a category with:

1. Objects: CohObject (§1)
2. Morphisms: CohMorphism (§4)
3. Identity and composition satisfying category laws

---

## Identity Morphism

For each object S, the identity morphism is:

```
id_S = (id_X, id_Rec)
```

where:
- id_X: X → X is the identity function on states
- id_Rec: Rec → Rec is the identity function on receipts

Satisfies M1 and M2 trivially.

---

## Composition

For morphisms:

```
f: S₁ → S₂  = (f_X, f_♯)
g: S₂ → S₃  = (g_X, g_♯)
```

Define composition:

```
g ∘ f = (g_X ∘ f_X, g_♯ ∘ f_♯)
```

The receipt map composes by substitution.

---

## Associativity

Composition is associative:

```
(h ∘ g) ∘ f = h ∘ (g ∘ f)
```

Follows from function composition associativity.

---

## Category Laws

| Law | Expression |
|-----|------------|
| Identity left | id ∘ f = f |
| Identity right | f ∘ id = f |
| Associativity | (h ∘ g) ∘ f = h ∘ (g ∘ f) |

---

## Implementation Notes

```python
class CohCategory:
    def id(self, obj: CohObject) -> CohMorphism:
        """§6.1: id_S = (id_X, id_Rec)"""
        return CohMorphism(
            state_map=lambda x: x,
            receipt_map=lambda rho: rho
        )
    
    def compose(self, f: CohMorphism, g: CohMorphism) -> CohMorphism:
        """§6.2: g ∘ f = (g_X ∘ f_X, g_♯ ∘ f_♯)"""
        return CohMorphism(
            state_map=lambda x: g.state_map(f.state_map(x)),
            receipt_map=lambda rho: g.receipt_map(f.receipt_map(rho))
        )
```

---

## Checked Composition

For testing and verification, use composition that validates axioms:

```python
def compose_checked(f, g, dom, mid, cod):
    """Compose with axiom verification"""
    result = compose(f, g)
    
    # Verify M1: admissibility preserved
    assert verify_admissibility_preservation(result, dom, cod)
    
    # Verify M2: receipt covariance
    assert verify_receipt_covariance(result, dom, cod)
    
    return result
```

---

## Conformance Points

| Law | Test |
|-----|------|
| Identity left | id ∘ f = f |
| Identity right | f ∘ id = f |
| Associativity | (h ∘ g) ∘ f = h ∘ (g ∘ f) |

---

---

## 6. Trace Closure Principle

**Specification v1.0.0 — §6**

Many Coh instances use "step receipts" as the morphisms of a time-indexed execution.

### Definition: Step Relation

Fix an object S = (X, V, RV). Define a step relation:

```
x → x'  (witnessed by receipt r)
```

This is equivalent to RV(x, r, x') = ACCEPT.

### Definition: Trace

A **trace** is a chain:

```
x₀ → x₁ → x₂ → ... → xₙ
   r₀    r₁    ...   rₙ₋₁
```

Written as:

```
x₀ ─r₀─→ x₁ ─r₁─→ x₂ ─...──→ xₙ
```

### Trace Closure Principle (Core)

**Legal steps compose into legal histories because receipts chain deterministically.**

Formally:
- Each receipt includes a **chain digest** linking to prior receipt
- Schema ID, policy ID, and canon profile hash are frozen
- The verifier can reconstruct and verify the entire chain from genesis

### Chain Digest Rule

For a receipt at step k, the chain digest is:

```
digest_k = hash(digest_{k-1} || schema_id || policy_hash || canon_profile_hash)
```

### Implementation

```python
def verify_trace_closure(obj, trace):
    """
    Verify that a complete trace is valid.
    
    Args:
        obj: Coh object
        trace: List of (state, receipt, state) tuples
    
    Returns:
        bool: True if trace is valid
    """
    # Check each step individually
    for i in range(len(trace) - 1):
        x, r, x_prime = trace[i], trace[i+1][0], trace[i+1][2]
        if not obj.validate(x, r, x_prime):
            return False
    
    # Verify chain linkage
    prior_digest = None
    for i, (x, r, x_prime) in enumerate(trace):
        current_digest = compute_digest(r, prior_digest)
        if not verify_digest_linkage(r, prior_digest):
            return False
        prior_digest = current_digest
    
    return True
```

### Corollary: Finite Descent Chains

Because V is bounded below (ℝ≥0) and each accepted transition decreases V (or increases by bounded budget), any trace must be finite. This prevents infinite descent.

---

## Notes

- The category structure ensures coherent composition of systems
- Morphisms preserve the algebraic-geometric binding (A2)
- Time evolution (functors) compose within this category structure
- Trace closure guarantees that valid histories can be replayed and verified
