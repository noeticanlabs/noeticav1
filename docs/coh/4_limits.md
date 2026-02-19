# Coh Limits

**Canonical ID:** `coh.category.v1`  
**Status:** Canonical  
**Section:** §7

---

## Products

Given objects S₁ and S₂, the product S₁ × S₂ is defined as follows.

### Geometry

```
X_× = X₁ × X₂

V_×(x₁, x₂) = V₁(x₁) + V₂(x₂)

C_× = C₁ × C₂
```

### Algebra

```
Rec_× = Rec₁ × Rec₂

Δ_×(ρ₁, ρ₂) = Δ₁(ρ₁) + Δ₂(ρ₂)
```

### Validator

```
RV_×((x₁, x₂), (y₁, y₂), (ρ₁, ρ₂))  ⟺  RV₁(x₁, y₁, ρ₁) ∧ RV₂(x₂, y₂, ρ₂)
```

The descent inequality holds by summation:

```
V_×(y₁, y₂) = V₁(y₁) + V₂(y₂)
            ≤ (V₁(x₁) + Δ₁(ρ₁)) + (V₂(x₂) + Δ₂(ρ₂))
            = V_×(x₁, x₂) + Δ_×(ρ₁, ρ₂)
```

### Universal Property

The product has projection morphisms:

```
π₁: S₁ × S₂ → S₁
π₂: S₁ × S₂ → S₂
```

For any object T with morphisms f₁: T → S₁ and f₂: T → S₂, there exists a unique morphism ⟨f₁, f₂⟩: T → S₁ × S₂ making the diagram commute.

---

## Pullbacks (Fiber Products)

Given morphisms:

```
p: S_A → S_O
l: S_B → S_O
```

The pullback S_A ×_{S_O} S_B is defined as follows.

### Geometry

```
X_pb = {(a, b) | p_X(a) = l_X(b)}
```

The subspace of X_A × X_B where projections agree.

### Algebra

```
Rec_pb = {(ρ_A, ρ_B) | p_♯(ρ_A) = l_♯(ρ_B)}
```

Receipts where projected receipts equal.

### Potential

```
V_pb(a, b) = V_A(a) + V_B(b)
```

Note: The condition p_X(a) = l_X(b) does NOT imply V_A(a) = V_B(b). The sum formula applies.

### Budget Map

```
Δ_pb(ρ_A, ρ_B) = Δ_A(ρ_A) + Δ_B(ρ_B)
```

### Validator

```
RV_pb((a₁, b₁), (a₂, b₂), (ρ_A, ρ_B))  ⟺
    RV_A(a₁, a₂, ρ_A) ∧
    RV_B(b₁, b₂, ρ_B) ∧
    p_♯(ρ_A) = l_♯(ρ_B)
```

The validator holds if both components are valid AND the projected receipts are equal.

### Universal Property

The pullback has projection morphisms:

```
π_A: S_pb → S_A
π_B: S_pb → S_B
```

For any object T with morphisms f_A: T → S_A and f_B: T → S_B satisfying p ∘ f_A = l ∘ f_B, there exists a unique morphism ⟨f_A, f_B⟩: T → S_pb making the diagram commute.

---

## Implementation Notes

### Product

```python
def product(obj1, obj2):
    X_product = product_space(obj1.X, obj2.X)
    Rec_product = product_space(obj1.Rec, obj2.Rec)
    
    def V_product(x_pair):
        return obj1.V(x_pair[0]) + obj2.V(x_pair[1])
    
    def Delta_product(rho_pair):
        return obj1.Delta(rho_pair[0]) + obj2.Delta(rho_pair[1])
    
    def RV_product(x1, y1, x2, y2, rho_pair):
        return obj1.RV(x1, y1, rho_pair[0]) and obj2.RV(x2, y2, rho_pair[1])
    
    return CohObject(...)
```

### Pullback

```python
def pullback(A, B, p, l):
    # X_pb = {(a,b) | p_X(a) = l_X(b)}
    X_pb = [(a, b) for a in A.X for b in B.X if p.state_map(a) == l.state_map(b)]
    
    # Rec_pb = {(ρ_A, ρ_B) | p_♯(ρ_A) = l_♯(ρ_B)}
    Rec_pb = [(ra, rb) for ra in A.Rec for rb in B.Rec 
              if p.receipt_map(ra) == l.receipt_map(rb)]
    
    def V_pb(pair):
        return A.V(pair[0]) + B.V(pair[1])
    
    return CohObject(...)
```

---

## Conformance Points

| Limit | Property |
|-------|----------|
| Product | V_×(x₁,x₂) = V₁(x₁) + V₂(x₂) |
| Product | RV_× = RV₁ ∧ RV₂ |
| Pullback | X_pb = {(a,b) | p_X(a) = l_X(b)} |
| Pullback | V_pb(a,b) = V_A(a) + V_B(b) |

---

## Notes

- Products and pullbacks ensure algebraic structure is preserved under combination
- The pullback implements the "observer space equality" pattern from CPS
- Both limits maintain the algebraic-geometric binding (A2)
