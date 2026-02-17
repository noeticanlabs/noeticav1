# CK-0 Tokenless Frontend Equivalence

**Version:** 1.0  
**Status:** Canonical  
**Related:** [`0_overview.md`](0_overview.md), [`K_join_semantics.md`](K_join_semantics.md), [`../nk3/1_canon_inputs.md`](../nk3/1_canon_inputs.md), [`../nk3/7_module_receipt.md`](../nk3/7_module_receipt.md)

---

## Overview

This document establishes tokenless as a **frontend equivalence milestone** for Phase 0 pre-build tightening. It defines the acceptability criterion for tokenless frontends and clarifies the distinction between frontend choice and execution semantics.

---

## 1. Canonical Input: NSC.v1 Bytes

### 1.1 Definition

NK-3 v1.0 takes **canonical NSC.v1 bytes** as its sole program input:

| Field | Type | Description |
|-------|------|-------------|
| `program_nsc_bytes` | bytes | Canonical NSC.v1 byte encoding |
| `program_nsc_digest` | Hash256 | H_R(program_nsc_bytes) |

### 1.2 No Frontend Degrees of Freedom

The NK-3 lowering core is **frontend-agnostic**. It accepts any input that produces valid canonical NSC.v1 bytes. The frontend's role is to translate from some source representation (tokens, AST, etc.) to these canonical bytes.

---

## 2. Tokenless as Frontend Choice

### 2.1 Not an Execution Choice

**Tokenless is a frontend implementation decision, not an execution semantics decision.**

- Tokenless frontends produce NSC.v1 bytes directly (no intermediate token representation)
- The NK-3 lowering core, NK-2 runtime, and NK-1 gate operate identically regardless of frontend choice
- Execution semantics are determined by the canonical NSC.v1 program, not by how it was produced

### 2.2 What Changes

| Aspect | Token Frontend | Tokenless Frontend |
|--------|----------------|-------------------|
| Input | Source text/tokens | Direct NSC.v1 construction |
| Output | NSC.v1 bytes | NSC.v1 bytes (same) |
| NK-3 input | NSC.v1 bytes | NSC.v1 bytes (same) |
| Runtime behavior | Identical | Identical |
| Receipt chain | Identical | Identical |

---

## 3. Frontend Acceptability Criterion

### 3.1 NSC Digest Equality

A frontend (token or tokenless) is **acceptable** iff it produces **identical canonical NSC.v1 bytes** for the **same program meaning**.

Formally:

```
Frontend F is acceptable ⇔
  ∀ programs P with meaning M:
    H_R(F(P)) = H_R(G(P'))
```

Where:
- `F` = candidate frontend
- `G` = reference frontend (produces canonical NSC.v1)
- `P` = source representation (tokens, text, AST, etc.)
- `M` = program meaning (semantics)
- `H_R` = canonical digest function

### 3.2 Gate NK-3.G1

This criterion is formalized as **Gate NK-3.G1**:

> A tokenless frontend is admitted iff it emits **identical canonical NSC.v1 bytes** for the same program meaning.

Equivalently: two programs have **equivalent frontend output** if and only if their `program_nsc_digest` values are equal.

---

## 4. ModuleReceipt Binding

### 4.1 Program Digest Commitment

The [`ModuleReceipt`](../nk3/7_module_receipt.md) binds the `program_nsc_digest`:

```python
@dataclass(frozen=True)
class ModuleReceipt:
    # Program binding
    program_nsc_digest: Hash256
    
    # Chain bindings
    policy_digest: Hash256
    kernel_registry_digest: Hash256
    
    # Artifact bindings
    opset_digest: Hash256
    dag_digest: Hash256
    execplan_digest: Hash256
```

### 4.2 Digest Equality Verification

Since ModuleReceipt commits to `program_nsc_digest`, any frontend producing the same digest yields:
- Identical OpSet
- Identical DAG
- Identical ExecPlan
- Identical verification path

This ensures **frontend equivalence is verifiable** through the receipt chain.

---

## 5. Phase Classification

### 5.1 Phase-1.5: Frontend Milestone

Tokenless is a **Phase-1.5 frontend milestone**, not a Phase-1 runtime milestone.

| Phase | Focus | Tokenless Status |
|-------|-------|-----------------|
| Phase 0 | Mathematical foundations (CK-0) | Pre-build tightening |
| Phase 1 | Runtime core (NK-1, NK-2, NK-3) | **NOT required** |
| Phase 1.5 | Frontend equivalence | Tokenless admitted |

### 5.2 Rationale

- **Runtime independence**: NK-3 lowering is identical regardless of frontend
- **Verification transparency**: ModuleReceipt binds digest, enabling frontend-agnostic verification
- **Incremental adoption**: Tokenless frontends can be developed independently of runtime milestones

---

## 6. Summary

| Property | Value |
|----------|-------|
| Canonical input | NSC.v1 bytes |
| Digest function | `program_nsc_digest = H_R(program_nsc_bytes)` |
| Tokenless criterion | Identical `program_nsc_digest` for same program meaning |
| Verification path | ModuleReceipt binds all digests |
| Phase placement | Phase-1.5 frontend milestone |

---

## Related Documents

- [`../nk3/1_canon_inputs.md`](../nk3/1_canon_inputs.md) — NK-3 Canon Inputs
- [`../nk3/7_module_receipt.md`](../nk3/7_module_receipt.md) — ModuleReceipt Schema
- [`../nk3/0_overview.md`](../nk3/0_overview.md) — NK-3 Overview (Tokenless Decision Gate)
