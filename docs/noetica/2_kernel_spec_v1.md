# Noetica Kernel Specification v1

**Version:** 1.0  
**Status:** Draft  
**Related:** [`1_language_model.md`](1_language_model.md), [`3_type_system.md`](3_type_system.md)

---

## 2.1 The 10 Constructs

Noetica Core v1 consists of exactly **10 kernel constructs**. No additional constructs are permitted. Each construct has precise static typing rules and operational semantics.

### Boundary Operations (Host Interface)

| Construct | Symbol | Description |
|-----------|--------|-------------|
| `mint` | `mint a from cap -> b` | Create budget from minting capacity |
| `burn` | `burn a -> r` | Destroy budget, produce receipt |
| `thaw` | `thaw lb -> b` | Convert locked budget to spendable |
| `measure` | `measure s -> m` | Read V(x) without modification |
| `emit_checkpoint` | `emit -> rc` | Produce state checkpoint receipt |

### Geometry Operations (PhaseLoom)

| Construct | Symbol | Description |
|-----------|--------|-------------|
| `solve` | `solve <b> x y -> x' y'` | Attempt gradient descent step |
| `repair` | `repair <b> x y -> x' y'` | Attempt curvature restoration |

### Phase Control

| Construct | Symbol | Description |
|-----------|--------|-------------|
| `freeze` | `freeze ls fs -> lbs` | Transition to Frozen phase |
| `phase_match` | `phase_match s { ... }` | Conditional based on phase |

### Linear Memory

| Construct | Symbol | Description |
|-----------|--------|-------------|
| `move` | `move x -> y` | Transfer linear resource |

### Sequencing

| Construct | Symbol | Description |
|-----------|--------|-------------|
| `;` | `e1; e2` | Sequential composition |

---

## 2.2 Static Typing Rules

Typing judgments are of the form:

```
Γ ⊢ e : τ
```

Where:
- **Γ** is the linear typing context (maps variables to types)
- **e** is an expression
- **τ** is the resulting type

### Context Operations

| Operation | Notation | Description |
|-----------|----------|-------------|
| Extension | `Γ, x:τ` | Add binding to context |
| Lookup | `Γ(x)` | Find type of variable |
| Empty | `·` | Empty context |

### Variables

```
Γ, x:τ ⊢ x : τ      (if x is last in context)
```

### Mint

```
Γ ⊢ mint a from cap -> x : Budget
─────────────────────────────────────────────
Precondition: a > 0, cap is MintCap
Effect: Creates new Budget of amount a
```

### Burn

```
Γ ⊢ burn a -> x : BurnReceipt
─────────────────────────────────────────────
Precondition: a ≤ budget available
Effect: Destroys a units, produces receipt
```

### Solve

```
Γ ⊢ solve <b> xs ys -> xs' ys' : (LoomState × LoomState)
────────────────────────────────────────────────────────────────
Precondition: phase = Loom, b > 0 (budget)
Effect: Attempts gradient descent, consumes b
Outcome: (xs', ys') where xs' = solve(xs, budget=b)
         Budget consumed: min(b, actual cost)
         Fails if V(xs') > V(xs) + b
```

### Repair

```
Γ ⊢ repair <b> xs ys -> xs' ys' : (LoomState × LoomState)
────────────────────────────────────────────────────────────────
Precondition: phase = Loom, b > 0
Effect: Attempts curvature restoration, consumes b
Outcome: (xs', ys') with improved curvature bound
```

### Freeze

```
Γ ⊢ freeze ls fs -> lbs : LockedBudget
─────────────────────────────────────────────
Precondition: ls: LoomState, fs: FrozenState
Effect: Locks both states, produces LockedBudget
Phase transition: Loom → Frozen
```

### Thaw

```
Γ ⊢ thaw lbs -> b : Budget
─────────────────────────────────────────────
Precondition: lbs: LockedBudget
Effect: Unlocks budget for spending
Phase transition: Frozen → Loom
```

### Measure

```
Γ ⊢ measure s -> m : Measurement
─────────────────────────────────────────────
Precondition: s is any state
Effect: Reads V(s) without modification
Result: m.value = V(s) in DebtUnit
```

### Emit Checkpoint

```
Γ ⊢ emit -> rc : CheckpointReceipt
─────────────────────────────────────────────
Precondition: phase = Frozen
Effect: Produces cryptographic receipt of current state
Receipt contains: state hash, V(x), timestamp
```

### Move

```
Γ ⊢ move x -> y : τ
─────────────────────────────────────────────
Precondition: x: τ where τ is linear
Effect: Transfers ownership from x to y
         x is consumed (cannot be used again)
```

### Phase Match

```
Γ ⊢ phase_match s { branch } : τ
─────────────────────────────────────────────
Precondition: s has phase tag
Effect: Executes branch based on current phase
         Only permitted branch type executed
```

---

## 2.3 Linear Typing Rules Summary

### Weakening (NOT PERMITTED)

```
Γ ⊢ e : τ
────────────────── ✗ Cannot drop linear variable
Γ, x:σ ⊢ e : τ
```

### Contraction (NOT PERMITTED)

```
Γ, x:τ, y:τ ⊢ e : σ
───────────────────── ✗ Cannot clone linear variable
Γ, x:τ ⊢ e : σ
```

### Exchange (PERMITTED)

```
Γ₁, x:τ, y:σ, Γ₂ ⊢ e : ρ
────────────────────────────────────
Γ₁, y:σ, x:τ, Γ₂ ⊢ e : ρ
```

---

## 2.4 Type Syntax

```
τ ::=                           // Types
    | Budget                    // Spendable currency
    | LockedBudget              // Frozen currency
    | MintCap                   // Minting authority
    | LoomState                 // Active geometric memory
    | FrozenState               // Immutable state
    | BurnReceipt               // Proof of burn
    | AuthReceipt               // Authority injection proof
    | Measurement               // V(x) reading
    | CheckpointReceipt         // State checkpoint proof
    | τ₁ → τ₂                   // Linear function
    | τ × τ                     // Product
    | unit                      // Sequencing unit

phase ::= Loom | Frozen
```

---

## 2.5 References

- Language model: [`1_language_model.md`](1_language_model.md)
- Type system: [`3_type_system.md`](3_type_system.md)
- Integration: [`integration_with_ck0_and_phaseloom.md`](integration_with_ck0_and_phaseloom.md)
- Formal targets: [`7_formal_targets.md`](7_formal_targets.md)
