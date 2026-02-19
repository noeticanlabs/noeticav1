# Noetica Type System

**Version:** 1.0  
**Status:** Draft  
**Related:** [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md), [`4_refinement_profile_v1.md`](4_refinement_profile_v1.md)

---

## 3.1 Linear Types

Noetica uses a **linear type system** to enforce resource conservation. Every linear resource must be used exactly once — no dropping, no cloning.

### Type Classification

| Type | Linear | Droppable | Cloneable | Description |
|------|--------|-----------|-----------|-------------|
| `Budget` | Yes | No | No | Spendable currency units |
| `LockedBudget` | Yes | No | No | Frozen currency, requires thaw |
| `MintCap` | Yes | No | No | Authority to mint new budget |
| `LoomState` | Yes | No | No | PhaseLoom geometric memory |
| `FrozenState` | Yes | No | No | Immutable checkpointed state |
| `BurnReceipt` | No | Yes | Yes | Proof of burn operation |
| `AuthReceipt` | No | Yes | Yes | Authority injection proof |
| `Measurement` | No | Yes | Yes | V(x) reading result |
| `CheckpointReceipt` | No | Yes | Yes | State checkpoint proof |
| `MintReceipt` | No | Yes | Yes | Proof of mint operation |

### Linear Type Rules

#### Consumption Requirement

```
Γ ⊢ e : τ    where τ is linear
─────────────────────────────────────────
The variable bound to τ in Γ must appear
exactly once in the evaluation of e
```

#### No Weakening

```
Γ ⊢ e : τ
───────────────────────────────── ✗ ILLEGAL
Γ, x:σ ⊢ e : τ
```

Adding a linear variable that is never used is a type error.

#### No Contraction

```
Γ, x:τ ⊢ e : σ
───────────────────────────────── ✗ ILLEGAL
Γ, x:τ, y:τ ⊢ e : σ   [where τ is linear]
```

Duplicating a linear variable is a type error.

#### Exchange

```
Γ₁, x:τ, y:σ, Γ₂ ⊢ e : ρ
──────────────────────────────────── ✓ LEGAL
Γ₁, y:σ, x:τ, Γ₂ ⊢ e : ρ
```

Reordering linear variables is permitted.

---

## 3.2 Phase Types

The system maintains a **phase distinction** between Loom and Frozen states.

### Phase Types

```
phase ::= Loom | Frozen
```

### Phase Exclusivity Theorem

```
LoomState ≠ FrozenState
```

**Theorem:** No program can call `solve` in Frozen phase.

**Proof Outline:**

1. By definition of Frozen phase, `loom_state = ⊥` (no geometric memory)
2. `solve` requires non-⊥ LoomState as precondition
3. Therefore `solve` cannot execute in Frozen phase
4. Attempting to do so produces a phase violation error at runtime

See: [`7_formal_targets.md`](7_formal_targets.md) for complete Lean formalization.

### Phase-Dependent Operations

| Operation | Loom | Frozen |
|-----------|------|--------|
| `solve` | ✓ | ✗ |
| `repair` | ✓ | ✗ |
| `freeze` | ✓ | ✓ (no-op) |
| `thaw` | ✓ (no-op) | ✓ |
| `measure` | ✓ | ✓ |
| `emit_checkpoint` | ✗ | ✓ |

---

## 3.3 Subtyping

### Budget Subtyping

```
LockedBudget <: Budget
```

A locked budget can be used wherever an unlocked budget is expected (after thaw).

### Phase Subtyping

```
Loom <: phase
Frozen <: phase
```

Both phases are subtypes of the abstract phase type.

### Non-Structural Subtyping

No structural subtyping. Types are nominal.

---

## 3.4 Effect System

### Effects

| Effect | Description |
|--------|-------------|
| `reads(σ)` | Reads state component σ |
| `writes(σ)` | Writes state component σ |
| `mint` | Creates new budget |
| `burn` | Destroys budget |
| `phase_transition` | Changes phase |
| `produces(ρ)` | Produces receipt ρ |

### Effect Polymorphism

Functions may be polymorphic over effects:

```
∀α. (Budget → Budget)    // Any budget-consuming function
```

---

## 3.5 Type Syntax (BNF)

```
type      ::= "Budget"
           | "LockedBudget"
           | "MintCap"
           | "LoomState"
           | "FrozenState"
           | "BurnReceipt"
           | "AuthReceipt"
           | "Measurement"
           | "CheckpointReceipt"
           | "MintReceipt"
           | type "→" type
           | type "×" type
           | "(" type ")"

phase     ::= "Loom" | "Frozen"

linearity ::= "linear" | "unrestricted"
```

---

## 3.6 Type Checking Algorithm

### Algorithm Overview

1. **Parse** source into AST
2. **Build** initial typing context from function parameters
3. **Walk** AST, applying typing rules
4. **Track** linear variable usage
5. **Reject** on violation of linearity or phase rules

### Linear Variable Tracking

```
UsageMap: Var → {once, many, unused}
```

| Usage | Valid for Linear | Valid for Non-Linear |
|-------|------------------|----------------------|
| `once` | ✓ | ✓ |
| `many` | ✗ | ✓ |
| `unused` | ✗ | ✓ |

---

## 3.7 References

- Kernel spec: [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)
- Refinement profile: [`4_refinement_profile_v1.md`](4_refinement_profile_v1.md)
- Formal targets: [`7_formal_targets.md`](7_formal_targets.md)
