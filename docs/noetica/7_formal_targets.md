# Noetica Formal Targets (Lean Proofs)

**Version:** 1.0  
**Status:** Draft  
**Related:** [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md), [`3_type_system.md`](3_type_system.md)

---

## 7.1 Lean Proof Targets

This document defines the formal verification targets for Noetica using Lean. These proofs ensure the language satisfies its design guarantees.

### Target Overview

| Target | Description | Status |
|--------|-------------|--------|
| T1 | Type soundness (progress + preservation) | Required |
| T2 | Linear conservation theorem | Required |
| T3 | Phase exclusion theorem | Required |
| T4 | Refinement admissibility preservation | Required |
| T5 | Conditional liveness (authority injection) | Required |

---

## T1: Type Soundness

### Statement

```
⊢⊢ ∀ (e : Expr) (Γ : Context) (τ : Type),
    Γ ⊢ e : τ → ∀ (σ : State), progress(e, Γ, σ)
```

Where:
- **Progress**: Either e is a value, or there exists σ' such that e steps to e' with σ'
- **Preservation**: If Γ ⊢ e : τ and e →* e' and σ →* σ', then Γ ⊢ e' : τ

### Progress Theorem

```
∀ e σ,  ⊢ e : τ → reducible(e) ∨ value(e)
```

A well-typed expression is either a value or can take a step.

### Preservation Theorem

```
∀ e e' σ σ' τ,
    ⊢ e : τ → e →* e' → σ →* σ'
    → ⊢ e' : τ
```

Well-typed expressions preserve their type through reduction.

---

## T2: Linear Conservation Theorem

### Statement

```
⊢⊢ ∀ (e : Expr) (Γ : Context) (τ : Type),
    Γ ⊢ e : τ → linear(τ) = true
    → resources(Γ) = resources(eval(e, Γ))
```

### Theorem

Every execution of a well-typed program preserves the total quantity of linear resources.

### Proof Sketch

1. **Base cases**: Each kernel construct is proven to preserve resources
2. **Inductive step**: If e₁ and e₂ preserve resources, then e₁; e₂ does too
3. **Lemma**: Each construct has a resource lemma (see below)

### Resource Lemmas

| Construct | Lemma |
|-----------|-------|
| `mint` | resources(Γ') = resources(Γ) + amount |
| `burn` | resources(Γ') = resources(Γ) - amount |
| `solve` | resources(Γ') = resources(Γ) - cost(solve) |
| `repair` | resources(Γ') = resources(Γ) - cost(repair) |
| `freeze` | resources(Γ') = resources(Γ) (reclassified) |
| `thaw` | resources(Γ') = resources(Γ) (reclassified) |
| `move` | resources(Γ') = resources(Γ) (transferred) |

---

## T3: Phase Exclusion Theorem

### Statement

```
⊢⊢ ∀ (e : Expr) (Γ : Context),
    Γ ⊢ e : τ → phase(e) = Loom → solve_reachable(e) = false
```

### Theorem

`solve` and `repair` operations cannot be reached from Frozen phase.

### Proof Outline

1. **Phase invariant**: The phase is part of the execution state
2. **Transition rules**: Only `freeze` and `thaw` change phase
3. **Guard**: `solve` checks `phase = Loom` before execution
4. **Conclusion**: If phase = Frozen, solve cannot execute

### Corollaries

```
solve_in_frozen : frozen(σ) → ¬can_solve(σ)
repair_in_frozen : frozen(σ) → ¬can_repair(σ)
```

---

## T4: Refinement Admissibility Preservation

### Statement

```
⊢⊢ ∀ (e : Expr) (σ σ' : State) (Θ : Threshold),
    σ ⊢ e →* σ'
    → V(σ') ≤ V(σ) + Θ
```

### Theorem

Every execution step maintains the refinement bound.

### Proof Sketch

1. **V(x) is non-increasing**: CK-0 guarantees V(x') ≤ V(x) for admissible steps
2. **Budget bound**: Each step consumes at most Θ budget
3. **Composition**: Sequence of steps composes the inequality

### Integration with CK-0

The refinement predicate maps to CK-0:

```
V(x) = Σ_k w_k · ||r_k(x)/σ_k(x)||²
```

See: [`../ck0/3_violation_functional.md`](../ck0/3_violation_functional.md)

---

## T5: Conditional Liveness (Authority Injection)

### Statement

```
⊢⊢ ∀ (σ : State) (a : Authority),
    admissible(σ)
    → can_inject_authority(σ, a)
    → eventually(σ', σ ⊢* σ' ∧ authority_applied(σ', a))
```

### Theorem

If the system is admissible and authority injection is possible, then eventually the authority will be applied.

### Conditions

- **Admissibility**: V(σ) ≤ ε₀ (within refinement bound)
- **Authority available**: Some AuthReceipt ρ is available
- **Budget sufficient**: Enough budget to process injection

### Reference to PhaseLoom

Authority injection uses the PhaseLoom mechanism:

- See: [`../phaseloom/9_authority_injection.md`](../phaseloom/9_authority_injection.md)

---

## 7.2 Lean Module Structure

```
noetica/
├── syntax/
│   ├── expr.lean      # Expression syntax
│   ├── context.lean   # Typing context
│   └── types.lean     # Type definitions
├── semantics/
│   ├── eval.lean      # Evaluation relation
│   ├── reduction.lean # Reduction rules
│   └── state.lean     # State definition
├── soundness/
│   ├── progress.lean   # Progress theorem
│   ├── preservation.lean # Preservation theorem
│   └── conservation.lean # Linear conservation
├── phase/
│   ├── phase_def.lean # Phase definitions
│   └── exclusion.lean # Phase exclusion
└── refinement/
    ├── admissibility.lean # Refinement preservation
    └── liveness.lean       # Conditional liveness
```

---

## 7.3 Dependencies on CK-0 and PhaseLoom

### CK-0 Dependencies

- **Violation functional V(x)**: From `ck0.violation`
- **DebtUnit arithmetic**: From `ck0.debtunit`
- **Curvature matrix M**: From `ck0.curvature`

### PhaseLoom Dependencies

- **PLState**: From `phaseloom.types`
- **V_PL**: From `phaseloom.potential`
- **Authority injection**: From `phaseloom.authority`

---

## 7.4 References

- Kernel spec: [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)
- Type system: [`3_type_system.md`](3_type_system.md)
- Refinement: [`4_refinement_profile_v1.md`](4_refinement_profile_v1.md)
- Integration: [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)
