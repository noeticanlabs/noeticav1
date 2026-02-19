# Coh v1.0

**Category of Coherent Spaces**

**Canonical ID:** `coh.category.v1`  
**Version:** `1.0.0`  
**Status:** Canonical Definition  
**Layer:** L1 (Mathematics)  
**Depends on:** None (foundational)

---

## Purpose

The category **Coh** formalizes systems that bind:

1. **Geometric state space** (X)
2. **Violation potential** (V: X → ℝ≥0)
3. **Algebra of certified transitions** (receipts: RV ⊆ X × X × Rec)

into a single categorical object supporting:

- Descent invariants
- Composition
- Limits (product, pullback)
- Functorial time (F: ℕ → Coh)
- Natural transformations (upgrades)

---

## Position in Architecture

```
┌─────────────────────────────────────────────┐
│           L1: Coh (Category Theory)          │
│  ┌─────────────────────────────────────────┐ │
│  │     Coh_CK0 (Full Subcategory)        │ │
│  │  - Specialized V: weighted residuals    │ │
│  │  - Specialized RV: receipt fields       │ │
│  └─────────────────────────────────────────┘ │
│                    ↓                          │
│     CK-0 (canonical semantic instance)       │
│                    ↓                          │
│  NEC → NK-1 → NK-2 → NK-3 (runtime)          │
└─────────────────────────────────────────────┘
```

### Relationship to CK-0

- **Coh** is the L1 category definition (type system)
- **CK-0** is a full subcategory (Coh_CK0) with:
  - Specialized V: weighted residual norm V(x) = r̃(x)ᵀW r̃(x)
  - Specialized RV: receipts with policy_id, budget, debt, residuals, hashes
  - Additional constraints: gate law, budget/debt update rules

---

## Document Spine

| Document | Content | Maps to Spec |
|----------|---------|--------------|
| [`1_objects.md`](1_objects.md) | 5-tuple definition, axioms A1-A3, bounded-tube | §1, §2, §3 |
| [`2_morphisms.md`](2_morphisms.md) | Morphism definition, M1-M2 | §4, §5 |
| [`3_category.md`](3_category.md) | Identity, composition, trace closure | §6 |
| [`4_limits.md`](4_limits.md) | Products, pullbacks | - |
| [`5_functors.md`](5_functors.md) | Functorial time, natural transformations | §8, §9 |
| [`6_ck0_integration.md`](6_ck0_integration.md) | Coh_CK0 subcategory | §8 |
| [`7_functors_builtin.md`](7_functors_builtin.md) | Vio, Adm, Transition functors | §2 |
| [`determinism_canon.md`](determinism_canon.md) | Determinism, serialization, proof obligations | §7, §12, §13 |
| [`universal_invariants.md`](universal_invariants.md) | System classification (conservative/dissipative/mixed) | §10 |
| [`module_interface_contract.md`](module_interface_contract.md) | Module surface area, receipts, test vectors | §11, §12 |
| [`8_examples.md`](8_examples.md) | 1D actuator + observer + pullback | Examples |
| [`9_reference_api.md`](9_reference_api.md) | Runtime API contract | Reference |

---

## Core Definitions

### Object (Definition §1, §2)

A Coh object can be represented in two equivalent forms:

**5-tuple form (canonical):**
```
S = (X, Rec, V, Δ, RV)
```

**3-tuple form (spec v1.0.0 simplified):**
```
S = (X, V, RV)
```

where:
- **X**: State space (set, optionally topological/measurable/manifold)
- **Rec**: Receipt set (algebraic witnesses) — implicit in 3-tuple form
- **V**: Potential functional V: X → ℝ≥0 (lower semicontinuous)
- **Δ**: Budget map Δ: Rec → ℝ≥0 — implicit in 3-tuple form (handled in RV)
- **RV**: Validator relation RV ⊆ X × X × Rec (or predicate in spec v1.0.0)

### Morphism (Definition §4)

A morphism f: S₁ → S₂ is a pair:

```
f = (f_X, f_♯)
```

where:
- **f_X**: X₁ → X₂ (state map)
- **f_♯**: Rec₁ → Rec₂ (receipt map)

---

## Categorical Properties

| Property | Status |
|----------|--------|
| Identity morphisms | §6.1 |
| Composition | §6.2 |
| Products | §7.1 |
| Pullbacks | §7.2 |
| Functorial time | §8 |
| Natural transformations | §9 |

---

## Final Status

Coh is:

- Well-defined
- Closed under products and pullbacks
- Supports functorial evolution
- Supports natural transformations
- Strictly binds algebra to geometry

No placeholders. No undefined components. No unstated assumptions.

This category is mathematically complete.
