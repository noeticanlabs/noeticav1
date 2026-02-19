# Coh Examples

**Canonical ID:** `coh.category.v1`  
**Status:** Examples  
**Purpose:** Illustrate categorical constructions

---

## Example 1: Simple Finite State System

### Setup

Consider a simple 3-state system with potential values:

```
States: {a, b, c}
V(a) = 0 (admissible)
V(b) = 1
V(c) = 2
```

### Object Definition

```python
# States
X = {'a', 'b', 'c'}

# Receipts (single trivial receipt)
Rec = {'ρ₀'}

# Potential
def V(x):
    return {'a': 0, 'b': 1, 'c': 2}[x]

# Budget
def Delta(rho):
    return 0

# Validator
def RV(x, y, rho):
    return (x, y) in {('b', 'a'), ('c', 'b')}  # descent only
```

### Properties

- Admissible set: C = {a}
- Transition relation: T = {(b, a), (c, b)}
- Descent preorder: a ≼ b ≼ c

---

## Example 2: 1D Actuator System

### Setup

A simple actuator with position and velocity:

```
State: x ∈ ℝ (position)
V(x) = x² (potential = squared distance from origin)
```

### Object Definition

```python
# State space: ℝ (represented as float)
def is_state(x):
    return isinstance(x, (int, float))

# Potential: quadratic
def V(x):
    return x ** 2

# Admissible: origin only
def is_admissible(x, eps=0.0):
    return abs(x) <= eps
```

### Transition

A transition from x to y is valid if it reduces potential:

```
RV(x, y, ρ) ⟺ V(y) ≤ V(x) + Δ(ρ)
```

---

## Example 3: Logic + Observer (Coupled System)

### Setup

Two systems that must agree on an "observer" value:

```
System A: states a₁, a₂ with values v₁, v₂
System B: states b₁, b₂ with values w₁, w₂
Observer O: value o
```

### Pullback Construction

Given morphisms:
- p: A → O (extracts observer value from A)
- l: B → O (extracts observer value from B)

The pullback A ×_O B represents states (a, b) where:

```
p_X(a) = l_X(b)  # observer values agree
```

### Implementation

```python
def observer_pullback(A, B, p, l):
    # X_pb = {(a,b) | p_X(a) = l_X(b)}
    X_pb = [(a, b) for a in A.X for b in B.X 
            if p.state_map(a) == l.state_map(b)]
    
    # V_pb(a,b) = V_A(a) + V_B(b)
    def V_pb(pair):
        return A.V(pair[0]) + B.V(pair[1])
    
    # Receipts where projected receipts equal
    Rec_pb = [(ra, rb) for ra in A.Rec for rb in B.Rec
              if p.receipt_map(ra) == l.receipt_map(rb)]
    
    return CohObject(...)
```

---

## Example 4: Time Evolution Functor

### Setup

A system that evolves over discrete time:

```
S₀: initial state
S₁: after one step
S₂: after two steps
```

### Functor Definition

```python
def time_functor():
    # Objects at each time step
    objects = {
        0: create_system(initial_state),
        1: create_system(after_one_step),
        2: create_system(after_two_steps)
    }
    
    # Morphisms (state evolution)
    morphisms = {
        (0, 1): evolution_step_0_to_1,
        (1, 2): evolution_step_1_to_2,
        (0, 2): evolution_composed  # = (1,2) ∘ (0,1)
    }
    
    return TimeFunctor(objects, morphisms)
```

### Properties

- Functor laws satisfied by construction
- Natural transformation can model "upgrade" from one evolution to another

---

## Example 5: Product of Systems

### Setup

Two independent systems combined:

```
System 1: (X₁, V₁, RV₁)
System 2: (X₂, V₂, RV₂)
```

### Product Construction

```python
def product_example():
    S1 = create_system_1()
    S2 = create_system_2()
    
    # Combined state space
    X_product = set.product(S1.X, S2.X)  # Cartesian product
    
    # Combined potential (sum)
    def V_combined(x1_x2):
        return S1.V(x1_x2[0]) + S2.V(x1_x2[1])
    
    # Combined admissible
    C_product = set.product(S1.C, S2.C)
    
    # Combined validator
    def RV_combined(x1, y1, x2, y2, rho_pair):
        return S1.RV(x1, y1, rho_pair[0]) and S2.RV(x2, y2, rho_pair[1])
    
    return CohObject(...)
```

---

## Example 6: CK-0 Compatible System

### Setup

A system satisfying CK-0 canonical form:

```
V(x) = r̃(x)ᵀ W r̃(x)  # weighted residual norm
Receipts have: policy_id, budget, debt, residual, hash
```

### CK-0 Object

```python
def create_ck0_system():
    # Weight matrix
    W = [[1.0, 0.0], [0.0, 1.0]]  # identity
    
    # Residual function
    def residual(x):
        return [x[0] - 1.0, x[1] - 2.0]  # distance from target (1, 2)
    
    # Potential = weighted residual norm
    def V(x):
        r = residual(x)
        return r[0]**2 + r[1]**2
    
    # Receipt schema
    def is_receipt(rho):
        return all(k in rho for k in ['policy_id', 'budget', 'debt', 'hash'])
    
    # Validator (CK-0 descent theorem)
    def validate(x, y, rho):
        return V(y) <= V(x) - rho['debt'] + rho['budget']
    
    return CohObject(
        is_state=lambda x: len(x) == 2,
        is_receipt=is_receipt,
        potential=V,
        budget_map=lambda rho: rho['budget'],
        validate=validate
    )
```

---

## Notes

- These examples illustrate the full range of Coh constructions
- Finite examples are testable; infinite examples (like ℝ) require approximation
- The CK-0 example shows how canonical form integrates into the general framework
