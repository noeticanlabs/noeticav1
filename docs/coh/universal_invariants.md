# Universal Invariants and System Classification

**Canonical ID:** `coh.category.v1`  
**Status:** Canonical  
**Section:** §10 (Coh Canon Specification v1.0.0)

---

## 1. Overview

Coh can classify systems structurally based on their invariance properties. This section defines the three main system classes that Coh can represent.

---

## 2. Conservative Systems

### Definition

A system is **conservative** if there exists a functional E such that along all legal transitions:

```
E(x') = E(x)
```

No monotone decrease is enforced — energy is preserved.

### Representation in Coh

To represent a conservative system:

- Choose V as a constant or invariant-aligned functional
- RV enforces invariance instead of descent
- The potential V does not necessarily decrease

### Example

```python
class ConservativeSystem:
    """System where energy is preserved."""
    
    def potential(self, x):
        # V is constant (or aligned with invariant)
        return 0.0
    
    def validate(self, x, r, x_prime):
        # Verify invariant E is preserved
        return self.invariant(x) == self.invariant(x_prime)
```

---

## 3. Dissipative Systems

### Definition

A system is **dissipative** (or governed) if legal transitions enforce:

```
V(x') ≤ V(x)
```

Or bounded increase with payment:

```
V(x') ≤ V(x) + Δ
```

where Δ is a bounded budget allowance.

### Representation in Coh

This is the standard CK-0 regime:

- V represents violation/energy
- RV enforces descent inequality
- Budget allows controlled increases

### Example

```python
class DissipativeSystem:
    """System where potential always decreases (or increases bounded by budget)."""
    
    def validate(self, x, r, x_prime):
        v_x = self.potential(x)
        v_x_prime = self.potential(x_prime)
        budget = r.get('budget', 0)
        
        # V(x') ≤ V(x) + budget
        return v_x_prime <= v_x + budget
```

---

## 4. Mixed Systems with Bounded Positive Variation

### Definition

A system is **mixed** if increases are allowed only via explicit authority/budget:

```
Σ max(V(x_{k+1}) - V(x_k), 0) ≤ Budget / κ
```

This ensures finite "risk fuel" — the total potential increase over a trace is bounded.

### Representation in Coh

- Track cumulative positive variation
- Enforce budget-based limits
- Enable "governed amplification"

### Example

```python
class MixedSystem:
    """System with bounded positive variation."""
    
    def __init__(self, budget, kappa=1.0):
        self.budget = budget
        self.kappa = kappa
    
    def validate(self, x, r, x_prime):
        v_x = self.potential(x)
        v_x_prime = self.potential(x_prime)
        
        increase = max(v_x_prime - v_x, 0)
        
        # Check cumulative bound
        if self.cumulative_increase + increase > self.budget / self.kappa:
            return False
        
        # Accept if within bounds
        self.cumulative_increase += increase
        return True
```

---

## 5. Classification Summary

| System Type | Invariant | Transition Rule |
|-------------|-----------|-----------------|
| Conservative | E(x') = E(x) | Invariant preserved |
| Dissipative | V(x') ≤ V(x) | Monotone decrease |
| Mixed | Σ max(ΔV, 0) ≤ B/κ | Bounded increase |

---

## 6. Choosing the Right Regime

| Regime | Use Case |
|--------|----------|
| Conservative | Physical systems with energy conservation, reversible computations |
| Dissipative | Error correction, repair systems, optimization |
| Mixed | Systems with both autonomous descent and intentional amplification |

---

## 7. Conformance

A Coh object must declare its system regime:

```python
def system_regime(obj):
    """
    Returns one of:
    - 'conservative': E preserved, no descent
    - 'dissipative': V decreases or bounded increase
    - 'mixed': Bounded positive variation
    """
    return obj.regime  # Must be declared
```

---

## References

- Coh Canon Specification v1.0.0 — §10
- CK-0 Service Law (for dissipative systems)
