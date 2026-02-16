# NK-3 Canon Outputs v1.0

**Version:** 1.0  
**Status:** Spec-closed  
**Related:** [`0_overview.md`](0_overview.md), [`1_canon_inputs.md`](1_canon_inputs.md)

---

## Overview

This document defines the canonical outputs that NK-3 must emit. All outputs are deterministic and hashable.

---

## 1. Output Summary

NK-3 produces four canonical artifacts:

| Artifact | Description |
|----------|-------------|
| OpSet | Deterministic list of OpSpecs sorted by op_id |
| DAG | Directed acyclic graph with hazard + control edges |
| ExecPlan | Policy-bound execution plan |
| ModuleReceipt | Binds all digests + toolchain IDs |

---

## 2. Canonical Encoding Profile

### 2.1 Profile Definition

All NK-3 artifacts use the **same ValueCanon profile** as NK-1:

| Property | Value |
|----------|-------|
| Profile ID | `id:nk1.valuecanon.v1` |
| Float rules | No NaN, no ±Inf |
| Map encoding | Sorted pair arrays |
| Set encoding | Sorted + deduped |

### 2.2 Canonicalization Rules

| Type | Rule |
|------|------|
| Arrays requiring set semantics | Sorted + deduped |
| Maps | Sorted by key, encoded as pair arrays |
| Floats | Forbidden (use DebtUnit rational) |
| Strings | UTF-8 encoded |

---

## 3. Digest Computation

### 3.1 Digest Algorithm

For each artifact A:

```
A_bytes := canon_bytes(A)
A_digest := H_R(A_bytes)
```

### 3.2 Hash Primitive

H_R is the hash primitive defined in PolicyBundle (SHA256 in v1.0).

---

## 4. Output Specifications

### 4.1 OpSet v1

A deterministic list of OpSpecs sorted by `op_id` bytes.

**Refer to:** [`4_opset.md`](4_opset.md)

### 4.2 DAG v1

A deterministic directed acyclic graph over OpIDs.

**Refer to:** [`5_dag.md`](5_dag.md)

### 4.3 ExecPlan v1

A policy-bound execution plan.

**Refer to:** [`6_execplan.md`](6_execplan.md)

### 4.4 ModuleReceipt v1

Binds all program and artifact digests.

**Refer to:** [`7_module_receipt.md`](7_module_receipt.md)

---

## 5. Output Validation

### 5.1 Schema Validation

Each output must validate against its schema:

| Artifact | Schema ID |
|----------|-----------|
| OpSet | `nk3.opset.v1` |
| DAG | `nk3.dag.v1` |
| ExecPlan | `nk3.execplan.v1` |
| ModuleReceipt | `nk3.module_receipt.v1` |

### 5.2 Determinism Verification

NK-3 must verify that:
- Same input bytes → identical output bytes
- All sorting is canonical (lexicographic)
- No floating-point values in output
- All sets are deduplicated

---

## 6. Artifact Dependencies

### 6.1 Dependency Graph

```
program_nsc_bytes
       │
       ▼
    ┌──────┐
    │ NK-3 │
    └──────┘
       │
       ├──────► OpSet ──────► opset_digest
       │
       ├──────► DAG ───────► dag_digest
       │
       ├──────► ExecPlan ──► execplan_digest
       │
       └──────► ModuleReceipt ──► module_receipt_digest
```

### 6.2 Digest Binding

ModuleReceipt must bind:
- `program_nsc_digest`
- `policy_digest`
- `kernel_registry_digest`
- `opset_digest`
- `dag_digest`
- `execplan_digest`
