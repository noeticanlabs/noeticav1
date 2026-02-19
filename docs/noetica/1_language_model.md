# Noetica Language Model

**Version:** 1.0  
**Status:** Draft  
**Related:** [`0_overview.md`](0_overview.md), [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)

---

## 1.1 Core Principles

Noetica enforces four fundamental invariants:

### Conservation (Linearity)

Every resource created must be consumed. No implicit drops, no cloning.

```
∀x. resources(x) = resources(x')  where x' is the result of executing x
```

### Admissibility (Refinement Inequality)

Every state transition must maintain the refinement bound:

```
V(x') ≤ V(x) + Θ  where Θ is the budget threshold from canonical_profile
```

### Phase Separation (Loom vs Frozen)

The system maintains two disjoint phase states:

- **Loom phase**: Geometric memory active, solve/repair operations permitted
- **Frozen phase**: Immutable, only measure and emit operations permitted

```
phase(x) ∈ {Loom, Frozen}
phase(x') = phase(x) unless freeze/thaw is explicitly invoked
```

### Boundary Purity

Host system calls (mint, burn, thaw, measure, emit_checkpoint) only occur at program boundaries. No host calls within loops.

---

## 1.2 Execution Model

### Program Structure

A Noetica program is a sequence of kernel expressions:

```
Program := ⟨expr₁; expr₂; ... exprₙ⟩
```

### Operational Semantics

Execution is defined as a state transition:

```
Env × Expr ──► Env'
```

Where **Env** contains:

| Component | Description |
|-----------|-------------|
| `budget` | Current spending budget (DebtUnit) |
| `loom_state` | PhaseLoom state (if in Loom phase) |
| `frozen_state` | Immutable state (if in Frozen phase) |
| `phase` | Current phase: Loom or Frozen |
| `receipts` | Accumulated receipt chain |
| `resources` | Linear resource context |

### Transition Rules

#### Conservation Law

```
Γ ⊢ e : Γ'
────────────────────
resources(Γ) = resources(Γ')
```

#### Refinement Law

```
Γ ⊢ e : Γ'
─────────────────────────────
V(Γ'.state) ≤ V(Γ.state) + Θ
```

#### Phase Law

```
Γ ⊢ freeze(e) : Γ'     ⇒  phase(Γ') = Frozen
Γ ⊢ thaw(e)   : Γ'     ⇒  phase(Γ') = Loom
Γ ⊢ e         : Γ'     ⇒  phase(Γ') = phase(Γ)  otherwise
```

---

## 1.3 Resource Model

### Linear Resources

The following are **linear resources** that must be consumed exactly once:

| Resource | Created By | Consumed By |
|----------|------------|-------------|
| `Budget` | `mint` | `burn`, `solve`, `repair` |
| `LockedBudget` | `freeze` | `thaw` |
| `MintCap` | (host) | `mint` |
| `LoomState` | (init) | `freeze` |
| `FrozenState` | `freeze` | `thaw` |

### Nonlinear Resources

These may be freely used (droppable, cloneable):

- `BurnReceipt` — proof of burn operation
- `AuthReceipt` — authority injection proof
- `Measurement` — V(x) measurement result
- `CheckpointReceipt` — state checkpoint proof

---

## 1.4 Phase Semantics

### Loom Phase

In Loom phase, the system has access to:

- Full PhaseLoom state (geometric memory)
- `solve` operation: Attempt gradient descent
- `repair` operation: Curvature restoration
- `freeze`: Transition to Frozen

### Frozen Phase

In Frozen phase:

- No solve/repair (would violate phase law)
- `measure`: Read V(x) without modification
- `emit_checkpoint`: Produce receipt
- `thaw`: Return to Loom phase

### Phase Transition Diagram

```
         ┌─────────┐
         │  Loom   │
         └────┬────┘
              │ freeze
              ▼
         ┌─────────┐
    ┌─── │ Frozen  │ ◄───┐
    │    └────┬────┘     │
    │         │ thaw     │
    └─────────┘          │
         (solve/repair   │
          prohibited)    │
```

---

## 1.5 Error Semantics

### Compile-Time Errors

| Error | Condition |
|-------|-----------|
| Linear variable unused | Resource created but not consumed |
| Linear variable duplicated | Attempt to clone linear resource |
| Phase violation | solve/repair in Frozen phase |
| Refinement unprovable | Predicate outside QF-LRA-FP |

### Runtime Errors (STF Rejection)

| Error | Condition |
|-------|-----------|
| Budget exhaustion | ΔV > remaining budget |
| Phase mismatch | Operation in wrong phase |
| Receipt hash mismatch | Digest verification failed |

---

## 1.6 References

- Kernel constructs: [`2_kernel_spec_v1.md`](2_kernel_spec_v1.md)
- Type system: [`3_type_system.md`](3_type_system.md)
- Refinement profile: [`4_refinement_profile_v1.md`](4_refinement_profile_v1.md)
- PhaseLoom integration: [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)
