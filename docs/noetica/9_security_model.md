# Noetica Security Model

**Version:** 1.0  
**Status:** Draft  
**Related:** [`8_wasm_abi_v1.md`](8_wasm_abi_v1.md), [`10_zero_cost_coherence.md`](10_zero_cost_coherence.md)

---

## 9.1 Adversary Model

Noetica assumes a powerful adversary with the following capabilities:

| Capability | Description |
|------------|-------------|
| Network control | Can intercept, modify, reorder messages |
| Code injection | Can submit arbitrary Noetica programs |
| State manipulation | Can attempt to corrupt local state |
| Timing attacks | Can measure execution timing |
| Budget cloning | Can attempt to double-spend |
| Replay | Can replay old receipts |
| Forge mint | Can attempt unauthorized minting |
| Phase escape | Can attempt to violate phase rules |
| Float injection | Can attempt to inject floating-point values |

---

## 9.2 Threat Analysis

### T1: Budget Cloning

**Attack**: Create budget that doesn't exist via linear type violation

**Mitigation**:
- Linear type system prevents duplication at compile time
- Runtime receipts prove each burn
- Hash chain ensures receipts can't be faked

**Severity**: Critical

### T2: Replay Attack

**Attack**: Replay old receipt to gain resources

**Mitigation**:
- Each receipt includes timestamp and sequence number
- Host maintains receipt log
- Duplicate detection at consensus layer

**Severity**: High

### T3: Forged Mint

**Attack**: Mint budget without proper authority

**Mitigation**:
- Mint requires valid MintCap
- MintCap is non-cloneable linear type
- Host verifies mint authority before execution

**Severity**: Critical

### T4: Phase Escape

**Attack**: Execute solve/repair in Frozen phase

**Mitigation**:
- Phase check at runtime
- Phase stored in typed state
- Phase exclusion theorem (T3) proves impossibility

**Severity**: High

### T5: Float Injection

**Attack**: Inject floating-point values into consensus path

**Mitigation**:
- No floats in consensus-critical code
- All values in DebtUnit (exact integer)
- Fixed-point encoding at WASM boundary

**Severity**: High

---

## 9.3 Defense Layers

### Compile-Time

| Defense | Target |
|---------|--------|
| Linear type system | Budget cloning |
| Phase type checking | Phase escape |
| Refinement fragment check | Complex predicates |

### Runtime

| Defense | Target |
|---------|--------|
| Phase checks | Phase escape |
| Budget tracking | Budget cloning |
| Receipt chain | Replay attacks |
| Domain separation | Hash collision |

### Host Layer

| Defense | Target |
|---------|--------|
| Authority verification | Forged mint |
| Receipt logging | Replay attacks |
| State validation | State corruption |

---

## 9.4 Security Properties

### SP1: Linear Conservation

```
∀ P, σ, σ'.  ⊢P →* σ'
  → resources(σ) = resources(σ')
```

No budget can be created or destroyed except through mint/burn.

### SP2: Phase Isolation

```
∀ P, σ, σ'.  ⊢P →* σ' ∧ frozen(σ)
  → ¬can_solve(σ')
```

Frozen phase cannot execute geometric operations.

### SP3: Deterministic Lowering

```
∀ P, H₁, H₂.  Lower(P, H₁) = Lower(P, H₂)
  → H₁ = H₂
```

Same program with same profile produces same WASM.

### SP4: Receipt Integrity

```
∀ r.  valid(r) → r.hash = Hash(r.contents)
```

Receipt hashes are collision-resistant (SHA-256).

### SP5: Refinement Bound

```
∀ P, σ, σ'.  ⊢P →* σ' → V(σ') ≤ V(σ) + Θ
```

All executions maintain refinement bound.

---

## 9.5 Attack Surface

### WASM Module

| Operation | Risk | Mitigation |
|-----------|------|------------|
| Local arithmetic | Low | Fixed operations |
| Memory access | Medium | Bounds checking |
| Control flow | Low | No indirect jumps |
| Host calls | High | Validation required |

### Host Boundary

| Operation | Risk | Mitigation |
|-----------|------|------------|
| mint | Critical | Authority check |
| burn | High | Receipt generation |
| thaw | Medium | State validation |
| measure | Low | Read-only |
| emit | Medium | Receipt signing |

---

## 9.6 Security Considerations for Deployment

### Isolation

- WASM modules should run in sandboxed environment
- No file system access
- No network access
- Limited memory (1GB max)

### Verification

- All receipts must be verified before acceptance
- Program hash must match stored hash
- Profile hash must be recognized

### Key Management

- Host signing keys must be protected
- Mint authority must be tightly controlled
- Receipt signing keys must be separate from mint authority

---

## 9.7 References

- WASM ABI: [`8_wasm_abi_v1.md`](8_wasm_abi_v1.md)
- Zero-cost coherence: [`10_zero_cost_coherence.md`](10_zero_cost_coherence.md)
- Formal targets: [`7_formal_targets.md`](7_formal_targets.md)
